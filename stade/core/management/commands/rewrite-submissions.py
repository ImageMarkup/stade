import csv
import functools
import io
import pathlib
from typing import BinaryIO, List, TextIO, Tuple
import zipfile

from django.core.files.base import ContentFile
import djclick as click
from isic_challenge_scoring import ClassificationScore
import numpy as np

from stade.core.models import Submission, Task

# TODO: test whether storage.open('r') works on both boto3 and minio
# TODO: 2016 BACC is always 1.0
# TODO: rescore doesn't allow different metrics


@click.command()
def rewrite_submissions():
    for task in Task.objects.filter(
        id__in=[
            39,  # 2016
            # 41,  # 2016b
            44,  # 44
            47,  # 47
        ]
    ):
        rewrite_task(task)


def rewrite_task(task: Task):
    dialect = task.challenge.slug

    with task.test_ground_truth_file.open() as gt_stream:
        gt_stream = rewrite(gt_stream, dialect)

    submissions = Submission.objects.filter(approach__task=task)

    old_sub_scores = {}
    new_sub_scores = {}

    for submission in submissions:
        old_sub_scores[submission.id] = submission.overall_score

        rewrite_submission(dialect, gt_stream, submission)

        new_sub_scores[submission.id] = submission.overall_score

    old_sub_scores = {
        item[0]: item[1]
        for item in sorted(old_sub_scores.items(), key=lambda item: item[1], reverse=True)
    }
    new_sub_scores = {
        item[0]: item[1]
        for item in sorted(new_sub_scores.items(), key=lambda item: item[1], reverse=True)
    }

    click.echo(old_sub_scores)
    click.echo(new_sub_scores)
    click.echo()
    if dialect != '2016':
        # The new algorithm for AP changed the ordering at the bottom of the leaderboard
        assert list(old_sub_scores.keys()) == list(new_sub_scores.keys())


def rewrite_submission(dialect: str, gt_stream: TextIO, submission: Submission) -> float:
    # Print old
    click.echo(submission.approach.name)
    click.echo(submission.test_prediction_file)
    click.echo(submission.overall_score)
    old_average_scores = [
        score['metrics'] for score in submission.score if score['dataset'] == 'Average'
    ][0]
    old_average_scores = {metric['name']: metric['value'] for metric in old_average_scores}
    old_aggregate_scores = [
        score['metrics'] for score in submission.score if score['dataset'] == 'aggregate'
    ][0]
    old_aggregate_scores = {metric['name']: metric['value'] for metric in old_aggregate_scores}

    # Rewrite and rescore
    if submission.test_prediction_file.name.endswith('.zip'):
        with submission.test_prediction_file.open() as prediction_stream:
            prediction_stream, prediction_file_name = from_zip(prediction_stream)
            prediction_stream = rewrite(prediction_stream, dialect)
    else:
        with submission.test_prediction_file.open() as prediction_stream:
            prediction_stream = rewrite(prediction_stream, dialect)
            prediction_file_name = submission.test_prediction_file.name.partition('/')[2]

    score = ClassificationScore.from_stream(gt_stream, prediction_stream)
    gt_stream.seek(0)
    prediction_stream.seek(0)

    assert score.overall == score.validation
    # Cannot assert that average precision is unchanged; sklearn changed their algorithm since
    # the original scoring
    if dialect == '2016':
        assert np.isclose(old_average_scores['area_under_roc'], score.macro_average['auc'])
        assert np.isclose(old_average_scores['accuracy'], score.macro_average['accuracy'])
    elif dialect == '2017':
        assert np.isclose(old_average_scores['area_under_roc_mean'], score.macro_average['auc'])
        assert np.isclose(old_average_scores['accuracy_mean'], score.macro_average['accuracy'])
        assert np.isclose(old_average_scores['accuracy_mean'], score.macro_average['accuracy'])
    elif dialect == '2018':
        assert np.isclose(old_average_scores['auc'], score.macro_average['auc'])
        assert np.isclose(old_average_scores['accuracy'], score.macro_average['accuracy'])
        assert np.isclose(
            old_aggregate_scores['balanced_accuracy'], score.aggregate['balanced_accuracy']
        )

    if dialect == '2016':
        submission.overall_score = score.macro_average['ap']
    elif dialect == '2017':
        submission.overall_score = score.macro_average['auc']
    elif dialect == '2018':
        submission.overall_score = score.aggregate['balanced_accuracy']
    else:
        raise Exception(f'Unknown dialect {dialect}')

    # Save updates
    submission.score = score.to_dict()
    submission.validation_score = submission.overall_score
    submission.test_prediction_file = ContentFile(
        prediction_stream.read().encode('utf-8'),
        name=prediction_file_name,
    )
    submission.save()

    # Print new
    click.echo(submission.overall_score)
    click.echo(old_average_scores)
    click.echo(score.macro_average.to_dict())
    click.echo()

    return submission.overall_score


@functools.lru_cache
def validation_images_2017() -> List[str]:
    with (
        pathlib.Path(__file__).parent / 'isic-2017-p3-validation-images.txt'
    ).open() as input_stream:
        images = [line.strip() for line in input_stream.readlines()]
        assert len(images) == 150
        return images


def rewrite(input_stream: BinaryIO, dialect) -> io.StringIO:
    # Enable automatic newline translation with newline=None
    text_input_stream = io.TextIOWrapper(input_stream, newline=None)
    csv_reader = csv.reader(text_input_stream)

    output_stream = io.StringIO(newline=None)
    csv_writer = csv.writer(output_stream)

    if dialect == '2016':
        csv_writer.writerow(['image', 'malignant'])
    elif dialect == '2017':
        csv_writer.writerow(['image', 'melanoma', 'seborrheic_keratosis'])
    for row in csv_reader:
        row = [field.strip() for field in row]
        # Remove empty fields
        row = [field for field in row if field]
        if not row:
            continue
        if dialect == '2017' and row[0] == 'image_id':
            continue

        # Some 2017 submissions included validation images
        if dialect == '2017' and row[0] in validation_images_2017():
            continue

        if dialect == '2016':
            assert len(row) == 2
            if row[1] == '0':
                row[1] = '0.0'
            elif row[1] == '1':
                row[1] = '1.0'
        elif dialect == '2017':
            assert len(row) == 3
        elif dialect == '2017':
            assert len(row) == 8

        csv_writer.writerow(row)

    output_stream.seek(0)
    return output_stream


def from_zip(input_stream: BinaryIO) -> Tuple[io.BytesIO, str]:
    zip_file = zipfile.ZipFile(input_stream)
    csv_infos = [
        zip_info
        for zip_info in zip_file.infolist()
        if zip_info.filename.endswith('.csv') and '__MACOSX' not in zip_info.filename
    ]
    assert len(csv_infos) == 1
    csv_info = csv_infos[0]

    output_stream = io.BytesIO()
    with zip_file.open(csv_info) as csv_stream:
        output_stream.write(csv_stream.read())
    output_stream.seek(0)
    return output_stream, csv_info.filename
