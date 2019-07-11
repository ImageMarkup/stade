from django.db import connection


def submissions_by_team(task_id):
    with connection.cursor() as cursor:
        cursor.execute(
            '''
SELECT
   submission_id
FROM
   (
      SELECT
         t.submission_id,
         ROW_NUMBER() OVER (PARTITION BY core_team.id ORDER BY t.overall_score DESC) AS tn
      FROM
         core_task,
         core_team,
         (
            SELECT
               core_approach.task_id,
               core_approach.team_id,
               core_submission.id AS submission_id,
               core_submission.overall_score,
               ROW_NUMBER() OVER (PARTITION BY core_approach.id ORDER BY core_submission.created DESC) AS rn
            FROM
               core_approach
               INNER JOIN
                  core_submission
                  ON core_submission.approach_id = core_approach.id
            WHERE
               core_submission.status = 'succeeded'
         )
         t
      WHERE
         core_task.id = t.task_id
         AND core_team.id = t.team_id
         AND t.task_id = %s
         AND t.rn = 1
   )
   f
WHERE
   tn = 1
            ''',
            [task_id],
        )
        return (row[0] for row in cursor.fetchall())


def submissions_by_approach(task_id):
    with connection.cursor() as cursor:
        cursor.execute(
            '''
SELECT
   t.submission_id
FROM
   core_task,
   (
      SELECT
         core_approach.task_id,
         core_submission.id AS submission_id,
         ROW_NUMBER() OVER (PARTITION BY core_approach.id ORDER BY core_submission.created DESC) AS rn
      FROM
         core_approach
         INNER JOIN
            core_submission
            ON core_submission.approach_id = core_approach.id
      WHERE
         core_submission.status = 'succeeded'
   )
   t
WHERE
   core_task.id = t.task_id
   AND t.task_id = %s
   AND t.rn = 1
            ''',
            [task_id],
        )
        return (row[0] for row in cursor.fetchall())
