#!/usr/bin/env python3
"""
Многопоточное чтение датчиков (USB-камера + SensorX) и отображение в окне.

- Каждый датчик читается в отдельном потоке постоянно (берём самые свежие данные).
- Обмен между потоками — через очереди (queue), хранится только последнее значение.
- В главном потоке с частотой отображения собираем кадр и рисуем поверх значения датчиков.
- Ресурсы (камера, окно) освобождаются по идиоме RAII (инициализация в __init__,
  освобождение в __del__).
- Ошибки логируются в папку log/ (модуль logging).
- Выход по клавише 'q'.
"""

import argparse
import logging
import os
import queue
import sys
import threading
import time

import cv2
import numpy as np


# --------------------------------------------------------------------------- #
#  Логирование
# --------------------------------------------------------------------------- #
def setup_logging() -> logging.Logger:
    """Настраивает логирование в файл log/app.log в текущем проекте."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(project_dir, "log")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    logger = logging.getLogger("sensors")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(threadName)s: %(message)s"
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # дублируем ошибки в консоль, чтобы их было видно сразу
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.WARNING)
    console.setFormatter(fmt)
    logger.addHandler(console)

    return logger


# --------------------------------------------------------------------------- #
#  Датчики
# --------------------------------------------------------------------------- #
class Sensor:
    def get(self):
        raise NotImplementedError("Subclasses must implement method get()")


class SensorX(Sensor):
    """Sensor X — имитация датчика, тикающего с заданной задержкой."""

    def __init__(self, delay: float):
        self._delay = delay
        self._data = 0

    def get(self) -> int:
        time.sleep(self._delay)
        self._data += 1
        return self._data


class SensorCam(Sensor):
    """
    Датчик USB-камеры. RAII: открытие в __init__, release() в __del__.
    """

    def __init__(self, cam_name, resolution):
        self._log = logging.getLogger("sensors")
        self._cap = None  # задаём заранее, чтобы __del__ не падал при ошибке init
        # имя камеры может быть индексом ("0") или путём ("/dev/video0")
        self._src = int(cam_name) if str(cam_name).isdigit() else cam_name
        self._width, self._height = resolution

        self._cap = cv2.VideoCapture(self._src)
        if not self._cap.isOpened():
            self._log.error("Камера '%s' не найдена / не открывается", cam_name)
            raise RuntimeError(f"Камера '{cam_name}' недоступна")

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        aw = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        ah = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if (aw, ah) != (self._width, self._height):
            self._log.warning(
                "Разрешение %dx%d не поддерживается, используется %dx%d",
                self._width, self._height, aw, ah,
            )
        self._log.info("Камера '%s' открыта (%dx%d)", cam_name, aw, ah)

    def _read(self):
        if self._cap is None or not self._cap.isOpened():
            return False, None
        return self._cap.read()

    def _reconnect(self) -> bool:
        """Пытается переоткрыть камеру (например, если её выдернули и вставили)."""
        for attempt in range(3):
            if self._cap is not None:
                self._cap.release()
            time.sleep(0.5)
            self._cap = cv2.VideoCapture(self._src)
            if self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
                self._log.info("Переподключение камеры удалось (попытка %d)", attempt + 1)
                return True
            self._log.warning("Переподключение не удалось (попытка %d)", attempt + 1)
        return False

    def get(self):
        ret, frame = self._read()
        if ret and frame is not None:
            return frame

        self._log.warning("Не удалось прочитать кадр, пробую переподключиться...")
        if self._reconnect():
            ret, frame = self._read()
            if ret and frame is not None:
                return frame

        self._log.error("Камера недоступна и не восстановлена (выдернули из USB?)")
        raise RuntimeError("Ошибка чтения с камеры, восстановление не удалось")

    def __del__(self):
        if getattr(self, "_cap", None) is not None:
            self._cap.release()
            self._cap = None
            logging.getLogger("sensors").info("Камера освобождена")


# --------------------------------------------------------------------------- #
#  Поток-обёртка над датчиком (читает постоянно, отдаёт последнее значение)
# --------------------------------------------------------------------------- #
class SensorThread:
    def __init__(self, sensor: Sensor, name: str,
                 stop_event: threading.Event, critical: bool = False):
        self._sensor = sensor
        self._name = name
        self._stop = stop_event
        self._critical = critical
        self._q: "queue.Queue" = queue.Queue(maxsize=1)
        self._log = logging.getLogger("sensors")
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)

    def start(self):
        self._thread.start()

    def _run(self):
        while not self._stop.is_set():
            try:
                data = self._sensor.get()
            except Exception as e:  # noqa: BLE001
                self._log.error("Датчик '%s' дал сбой: %s", self._name, e)
                if self._critical:
                    self._log.error("Критический датчик отказал — завершаем работу")
                    self._stop.set()
                break
            # храним только самое свежее значение
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._q.put_nowait(data)
            except queue.Full:
                pass

    def get(self, default=None):
        """Свежее значение или default, если нового нет."""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return default

    def join(self, timeout: float = 2.0):
        if self._thread.is_alive():
            self._thread.join(timeout=timeout)


# --------------------------------------------------------------------------- #
#  Окно отображения (RAII)
# --------------------------------------------------------------------------- #
class WindowImage:
    def __init__(self, freq: float):
        self._log = logging.getLogger("sensors")
        self._freq = max(1.0, float(freq))
        self._win = "Camera + Sensors"
        try:
            cv2.namedWindow(self._win, cv2.WINDOW_AUTOSIZE)
        except cv2.error as e:
            self._log.error("Не удалось создать окно: %s", e)
            raise

    @property
    def delay_ms(self) -> int:
        return max(1, int(1000.0 / self._freq))

    def show(self, img):
        try:
            cv2.imshow(self._win, img)
        except cv2.error as e:
            self._log.error("Не удалось вывести изображение: %s", e)
            raise

    def __del__(self):
        try:
            cv2.destroyWindow(self._win)
            logging.getLogger("sensors").info("Окно закрыто")
        except cv2.error:
            pass


# --------------------------------------------------------------------------- #
#  Отрисовка значений датчиков поверх кадра
# --------------------------------------------------------------------------- #
def draw_overlay(frame, values):
    """values: список кортежей (label, value). Рисует в правом нижнем углу."""
    h, w = frame.shape[:2]
    lines = [f"{label}: {val}" for label, val in values]

    font = cv2.FONT_HERSHEY_SIMPLEX
    scale, thick, pad, line_h = 0.5, 1, 6, 18

    box_w = max((cv2.getTextSize(t, font, scale, thick)[0][0] for t in lines),
                default=0) + 2 * pad
    box_h = line_h * len(lines) + 2 * pad
    x0 = max(0, w - box_w - 10)
    y0 = max(0, h - box_h - 10)

    overlay = frame.copy()
    cv2.rectangle(overlay, (x0, y0), (x0 + box_w, y0 + box_h), (255, 255, 255), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.rectangle(frame, (x0, y0), (x0 + box_w, y0 + box_h), (0, 0, 0), 1)

    for i, t in enumerate(lines):
        y = y0 + pad + line_h * (i + 1) - 4
        cv2.putText(frame, t, (x0 + pad, y), font, scale, (0, 0, 0), thick, cv2.LINE_AA)
    return frame


# --------------------------------------------------------------------------- #
#  Аргументы командной строки
# --------------------------------------------------------------------------- #
def parse_resolution(s: str):
    try:
        w, h = s.lower().split("x")
        return int(w), int(h)
    except Exception:
        raise ValueError(f"Некорректное разрешение '{s}', ожидается WxH (например 1280x720)")


def parse_args():
    p = argparse.ArgumentParser(
        description="Многопоточное чтение датчиков и камеры с выводом в окно"
    )
    p.add_argument("-c", "--camera", default="0",
                   help="Имя/индекс камеры в системе (например 0 или /dev/video0)")
    p.add_argument("-r", "--resolution", default="1280x720",
                   help="Желаемое разрешение камеры, например 1280x720")
    p.add_argument("-f", "--freq", type=float, default=30.0,
                   help="Частота отображения картинки, Гц")
    return p.parse_args()


# --------------------------------------------------------------------------- #
#  main
# --------------------------------------------------------------------------- #
def main() -> int:
    args = parse_args()
    log = setup_logging()
    log.info("Запуск приложения")

    try:
        resolution = parse_resolution(args.resolution)
    except ValueError as e:
        log.error("%s", e)
        print(e, file=sys.stderr)
        return 1

    stop_event = threading.Event()

    # --- камера (RAII) ---
    try:
        cam = SensorCam(args.camera, resolution)
    except Exception as e:  # noqa: BLE001
        log.error("Ошибка инициализации камеры: %s", e)
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1

    # --- датчики 100 Hz, 10 Hz, 1 Hz ---
    sensors = [
        SensorThread(SensorX(0.01), "Sensor0", stop_event),
        SensorThread(SensorX(0.1), "Sensor1", stop_event),
        SensorThread(SensorX(1.0), "Sensor2", stop_event),
    ]
    cam_thread = SensorThread(cam, "Camera", stop_event, critical=True)

    # --- окно (RAII) ---
    try:
        window = WindowImage(args.freq)
    except Exception as e:  # noqa: BLE001
        log.error("Ошибка инициализации окна: %s", e)
        cam_thread = None
        del cam
        return 1

    for s in sensors:
        s.start()
    cam_thread.start()

    last_frame = None
    last_vals = [0, 0, 0]

    try:
        while not stop_event.is_set():
            # самые свежие данные; если новых нет — оставляем предыдущие
            frame = cam_thread.get(default=None)
            if frame is not None:
                last_frame = frame
            for i, s in enumerate(sensors):
                v = s.get(default=None)
                if v is not None:
                    last_vals[i] = v

            if last_frame is None:
                disp = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
                cv2.putText(disp, "Ожидание камеры...", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            else:
                disp = last_frame.copy()

            draw_overlay(disp, [("Sensor0", last_vals[0]),
                                ("Sensor1", last_vals[1]),
                                ("Sensor2", last_vals[2])])
            try:
                window.show(disp)
            except Exception:  # noqa: BLE001
                break

            if (cv2.waitKey(window.delay_ms) & 0xFF) == ord("q"):
                log.info("Нажата 'q', выходим")
                break
    except KeyboardInterrupt:
        log.info("Прервано пользователем")
    finally:
        # корректное завершение и освобождение ресурсов (RAII)
        stop_event.set()
        for s in sensors:
            s.join()
        cam_thread.join()
        del window      # __del__ -> destroyWindow
        del cam_thread  # отпускаем ссылку на камеру из потока
        del cam         # __del__ -> cap.release()
        cv2.destroyAllWindows()
        log.info("Приложение остановлено")

    return 0


if __name__ == "__main__":
    sys.exit(main())
