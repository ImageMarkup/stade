import os
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from core.models import Submission
from core.tasks import _field_file_to_local_path


class Command(BaseCommand):
    help = 'Generate fake data for development'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        from zipfile import ZipFile

        # order by created in case of conflicting approach manuscripts
        for s in Submission.objects.filter(approach__task_id=51).order_by('created'):
            printed_stuff = False
            # print(s.id)

            if s.test_prediction_file.name.endswith('.zip'):
                with _field_file_to_local_path(s.test_prediction_file) as infile:
                    with ZipFile(infile) as z:
                        # z.printdir()
                        files = [f for f in z.namelist() if 'MACOSX' not in f]

                        csvs = [x for x in files if x.endswith('.csv')]
                        pdfs = [x for x in files if x.endswith('.pdf')]

                        if len(csvs) == 1:
                            if len(pdfs) == 1:
                                pdf = z.extract(pdfs[0])
                                pdf_filename = f'{uuid4()}/{os.path.basename(pdf)}'
                                s.approach.manuscript = SimpleUploadedFile(
                                    pdf_filename, open(pdf, 'rb').read(), 'application/pdf'
                                )
                                s.approach.save()
                            elif len(pdfs) != 0:
                                print(f'{s.id} - num pdfs {len(pdfs)}')
                                printed_stuff = True

                            csv = z.extract(csvs[0])
                            csv_filename = f'{uuid4()}/{os.path.basename(csv)}'
                            s.test_prediction_file = SimpleUploadedFile(
                                csv_filename, open(csv, 'rb').read(), 'text/plain'
                            )
                            s.save()
                        else:
                            print(f'{s.id} - num csvs {len(csvs)}')
                            printed_stuff = True

                        if printed_stuff:
                            z.printdir()
