"""冻结程序的入口：保留退出码，并兼容 Windows 多进程启动。"""

from multiprocessing import freeze_support


if __name__ == "__main__":
    freeze_support()

    import sys
    if len(sys.argv) == 4 and sys.argv[1] == "--verify-pixel-codecs":
        from qt_dicom_viewer.core.codec_check import verify
        raise SystemExit(verify(sys.argv[2], sys.argv[3]))

    from qt_dicom_viewer.app import main

    raise SystemExit(main())
