# Building RAPT for Windows

Use a clean Python environment on Windows. Python 3.11 is the safest target for the
current dependency set.

## 1. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If this fails, resolve the missing package first before continuing.

## 2. Smoke-check imports

```powershell
python -c "import PyQt6, qfluentwidgets, cv2, h5py, uhf.reader; print('imports ok')"
```

## 3. Build the executable

The first build should use the checked-in `onedir` spec:

```powershell
python -m PyInstaller --noconfirm --clean RAPT.spec
```

The output executable will be:

```text
dist\RAPT\RAPT.exe
```

Do not use `dist\main.exe`. That is stale output from an older CLI-oriented
build and is not the GUI application.

Keep `config.json` and `binding.json` next to `RAPT.exe`. The app writes runtime
configuration, tag bindings, and relative data output under the executable
directory when packaged.

## 4. Optional icon

PyInstaller on Windows expects an `.ico` file for the executable icon. Convert
`src/resources/RAPT_icon.png` to `src/resources/RAPT_icon.ico`, then add this to
the `EXE(...)` section in `RAPT.spec`:

```python
icon="src/resources/RAPT_icon.ico",
```
