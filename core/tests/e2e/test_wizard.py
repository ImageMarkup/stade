from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from core.models import Task
from core.tests.factories import TaskFactory


@pytest.fixture
@pytest.mark.transactional_db
def task(request):
    t: Task = TaskFactory(
        challenge__name='foo', challenge__locked=False, hidden=False, locked=False
    )

    with open(request.fspath.join('../../../../etc/data/example_groundtruth.csv'), 'rb') as infile:
        t.test_ground_truth_file = SimpleUploadedFile('groundtruth.csv', infile.read())

    t.save()

    yield t


def test_submission_wizard(request, selenium, live_server, django_user_model, tmpdir, task):
    django_user_model.objects.create_user(username='someone', password='something')

    # login user
    selenium.get(live_server.url)
    selenium.find_element_by_id('login-button').click()
    el = selenium.find_element_by_xpath('//input[@id="id_login"]')
    el.send_keys('someone')
    el = selenium.find_element_by_xpath('//input[@id="id_password"]')
    el.send_keys('something')
    selenium.find_element_by_id('log-in-submit').click()

    # create a new submission
    el = selenium.find_element_by_css_selector('.task.column')
    el.click()
    el = selenium.find_element_by_css_selector('.create-submission > a')
    el.click()

    # step 1) create a new team
    selenium.find_element_by_id('id_name').send_keys('Test team')
    selenium.find_element_by_id('id_institution').send_keys('Test institution')
    selenium.find_element_by_id('id_institution_url').send_keys('http://someurl.com')
    selenium.find_element_by_id('create-team-submit').click()

    # step 2) create a new approach
    pdf = tmpdir.join('test-approach.pdf')
    pdf.write('somefakecontent')
    selenium.find_element_by_id('id_name').send_keys('Test approach')
    selenium.find_element_by_id('id_manuscript').send_keys(pdf.strpath)
    selenium.find_element_by_id('create-approach-submit').click()

    # step 3) upload a submission file
    submission_file = request.fspath.join('../../../../etc/data/example_prediction.csv')
    selenium.find_element_by_id('id_accepted_terms').click()
    selenium.find_element_by_id('id_test_prediction_file').send_keys(submission_file.strpath)
    selenium.find_element_by_id('create-submission-submit').click()

    assert selenium.find_element_by_css_selector('li.status').text == 'Status: Queued for scoring'
