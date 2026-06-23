# -*- coding: utf-8 -*-
import django.db.models.deletion
from django.db import migrations, models


def _column_exists(cursor, table, column):
    cursor.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        [table, column],
    )
    return cursor.fetchone() is not None


def _table_exists(cursor, table):
    cursor.execute("SELECT to_regclass(%s)", [table])
    return cursor.fetchone()[0] is not None


def forward_merge(apps, schema_editor):
    """幂等合并：兼容部分执行后的数据库状态。"""
    DramaProject = apps.get_model("drama", "DramaProject")
    Project = apps.get_model("creation", "Project")
    connection = schema_editor.connection

    child_tables = [
        "drama_role_execution",
        "drama_episode_artifact",
        "drama_episode_quality",
        "drama_episode_plan",
        "drama_generation_plan",
    ]

    with connection.cursor() as cursor:
        for table in child_tables:
            if not _column_exists(cursor, table, "project_id"):
                cursor.execute(
                    f'ALTER TABLE "{table}" ADD COLUMN "project_id" uuid NULL'
                )
                cursor.execute(
                    f"""
                    ALTER TABLE "{table}"
                    ADD CONSTRAINT "{table}_project_id_fk"
                    FOREIGN KEY ("project_id") REFERENCES "creation_project" ("id")
                    DEFERRABLE INITIALLY DEFERRED
                    """
                )

        has_drama_table = _table_exists(cursor, "drama_project")

    if has_drama_table:
        for dp in DramaProject.objects.all().iterator():
            creation_id = dp.project_id
            try:
                project = Project.objects.get(pk=creation_id)
                project.track_mode = dp.track_mode or ""
                project.drama_stage = dp.current_stage or "strategy"
                project.completed_roles = dp.completed_roles or []
                project.word_count_stats = dp.word_count_stats or {}
                project.quality_scores = dp.quality_scores or {}
                project.delivery_status = dp.delivery_status or "pending"
                project.total_tokens_used = dp.total_tokens_used or 0
                project.total_cost_cents = dp.total_cost_cents or 0
                if dp.title and not (project.title or "").strip():
                    project.title = dp.title
                if dp.genre_code and not (project.theme or "").strip():
                    project.theme = dp.genre_code
                if dp.total_episodes and not project.episode_count:
                    project.episode_count = dp.total_episodes
                if dp.target_platform and not (project.target_platform or "").strip():
                    project.target_platform = dp.target_platform
                project.save()
            except Project.DoesNotExist:
                Project.objects.create(
                    id=creation_id,
                    user_id=dp.user_id,
                    theme=dp.genre_code or "family-revenge",
                    core_idea=(dp.title or "").strip() or "drama workspace",
                    episode_count=dp.total_episodes or 30,
                    target_platform=dp.target_platform or "douyin",
                    title=dp.title or "",
                    pipeline_mode="workspace",
                    creation_entry="from-scratch",
                    track_mode=dp.track_mode or "fast",
                    drama_stage=dp.current_stage or "strategy",
                    completed_roles=dp.completed_roles or [],
                    word_count_stats=dp.word_count_stats or {},
                    quality_scores=dp.quality_scores or {},
                    delivery_status=dp.delivery_status or "pending",
                    total_tokens_used=dp.total_tokens_used or 0,
                    total_cost_cents=dp.total_cost_cents or 0,
                )

            table_map = {
                "DramaRoleExecution": "drama_role_execution",
                "DramaEpisodeArtifact": "drama_episode_artifact",
                "DramaEpisodeQuality": "drama_episode_quality",
                "DramaEpisodePlan": "drama_episode_plan",
                "DramaGenerationPlan": "drama_generation_plan",
            }
            with connection.cursor() as cursor:
                for model_name, table in table_map.items():
                    if _column_exists(cursor, table, "drama_project_id"):
                        cursor.execute(
                            f'UPDATE "{table}" SET project_id = %s WHERE drama_project_id = %s',
                            [creation_id, dp.id],
                        )

    with connection.cursor() as cursor:
        for table in child_tables:
            if _column_exists(cursor, table, "drama_project_id"):
                cursor.execute(
                    f"""
                    UPDATE "{table}"
                    SET project_id = drama_project_id
                    WHERE project_id IS NULL AND drama_project_id IS NOT NULL
                    """
                )
                cursor.execute(
                    f'ALTER TABLE "{table}" DROP COLUMN IF EXISTS "drama_project_id" CASCADE'
                )
            if _column_exists(cursor, table, "project_id"):
                cursor.execute(
                    f'ALTER TABLE "{table}" ALTER COLUMN "project_id" SET NOT NULL'
                )
        if _table_exists(cursor, "drama_project"):
            cursor.execute('DROP TABLE IF EXISTS "drama_project" CASCADE')


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("creation", "0029_project_drama_workspace_fields"),
        ("drama", "0004_expand_genre_code_max_length"),
    ]

    operations = [
        migrations.RunPython(forward_merge, noop_reverse),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(model_name="dramaepisodeartifact", name="drama_project"),
                migrations.RemoveField(model_name="dramaepisodequality", name="drama_project"),
                migrations.RemoveField(model_name="dramaepisodeplan", name="drama_project"),
                migrations.RemoveField(model_name="dramagenerationplan", name="drama_project"),
                migrations.RemoveField(model_name="dramaroleexecution", name="drama_project"),
                migrations.AddField(
                    model_name="dramaepisodeartifact",
                    name="project",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drama_episode_artifacts",
                        to="creation.project",
                        verbose_name="剧本项目",
                    ),
                ),
                migrations.AddField(
                    model_name="dramaepisodequality",
                    name="project",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drama_episode_qualities",
                        to="creation.project",
                        verbose_name="剧本项目",
                    ),
                ),
                migrations.AddField(
                    model_name="dramaepisodeplan",
                    name="project",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drama_episode_plans",
                        to="creation.project",
                        verbose_name="剧本项目",
                    ),
                ),
                migrations.AddField(
                    model_name="dramagenerationplan",
                    name="project",
                    field=models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drama_generation_plan",
                        to="creation.project",
                        verbose_name="剧本项目",
                    ),
                ),
                migrations.AddField(
                    model_name="dramaroleexecution",
                    name="project",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drama_role_executions",
                        to="creation.project",
                        verbose_name="剧本项目",
                    ),
                ),
                migrations.DeleteModel(name="DramaProject"),
            ],
        ),
    ]
