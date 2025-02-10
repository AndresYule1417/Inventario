import subprocess
import os

class LibreOfficeConverter:
    def __init__(self, libreoffice_path='libreoffice'):
        self.libreoffice_path = libreoffice_path

    def convert_to_pdf(self, input_file, output_file=None):
        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + '.pdf'
        subprocess.run([self.libreoffice_path, '--headless', '--convert-to', 'pdf', '--outdir', os.path.dirname(output_file), input_file])
        return output_file

    def convert_to_excel(self, input_file, output_file=None):
        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + '.xlsx'
        subprocess.run([self.libreoffice_path, '--headless', '--convert-to', 'xlsx', '--outdir', os.path.dirname(output_file), input_file])
        return output_file