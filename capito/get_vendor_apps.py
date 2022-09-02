import os
import platform
import zipfile
from pathlib import Path
from urllib import request


def download_and_unpack_ffmpeg():
    """Donload and unpack ffmpeg."""
    operating_system = platform.system()

    print("\nDownloading (and unpacking) ffmpeg into capito/vendor/ffmpeg\n")
    print("This may take a while...\n")

    vendor_dir = Path(os.environ["CAPITO_BASE_DIR"], "vendor")
    final_name = "ffmpeg"
    remote_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    if operating_system == "Linux":
        remote_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    elif operating_system == "Darwin":
        remote_url = "https://evermeet.cx/ffmpeg/ffmpeg-107921-ga51bdbb069.7z"

    download_path = vendor_dir
    extraction_path = vendor_dir
    download_path.mkdir(parents=True, exist_ok=True)
    extraction_path.mkdir(parents=True, exist_ok=True)

    request.urlretrieve(remote_url, download_path / "ffmpeg")

    downloaded_file = download_path / "ffmpeg"

    if operating_system in ["Linux", "Darwin"]:
        print(
            """
        ############################################################################
        #  Automatic unpacking currently only works for Windows.                   #
        #  For Linux and MacOS please install ffmpeg manually and add it to your   #
        #  system path. The installer will download your version into:             #
        #                                                                          #
        #                      ---->   capito/vendor/  <-----                      #
        #                                                                          #
        #  FFMPEG should be accessible in a shell by just typing 'ffmpeg'.         #
        #  This means you have to add it to your 'path' environment variable.      #
        #  On Linux/MacOS use the terminal and the 'export' command:               #
        #                                                                          #
        #              > export PATH="install/path/to/ffmpeg:$PATH"                #
        #                                                                          #
        #  If you skip this step the capito mp4 renderer will not work.            #
        #  The rest of capito framework will work as expected.                     #
        ############################################################################
        """
        )
        return

    # Windows only from here on...
    with zipfile.ZipFile(downloaded_file, "r") as zip_ref:
        zip_ref.extractall(extraction_path)

    extracted_file = Path(extraction_path / zip_ref.namelist()[0])
    # downloaded_file.unlink()
    # extracted_file.rename(extracted_file.with_name(final_name))
    print("\nCapito and 3rd party components downloaded and unpacked successfully!\n")


download_and_unpack_ffmpeg()
