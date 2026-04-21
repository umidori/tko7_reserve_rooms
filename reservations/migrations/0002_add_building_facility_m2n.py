# Generated manually – 2026-04-21
# 追加内容:
#   T-02 Building（buildings テーブル）
#   T-04 Facility（facilities テーブル）
#   T-05 Room の建物フィールドを CharField → FK(Building) に変更
#         rooms テーブルにリネーム
#   T-06 RoomFacility（room_facilities 中間テーブル）
#   T-07 DepartmentRoom（department_rooms テーブル）

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_department_options'),
        ('reservations', '0001_initial'),
    ]

    operations = [

        # ── T-02 建物マスタ ──────────────────────────────────────
        migrations.CreateModel(
            name='Building',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='建物名称')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成日時')),
            ],
            options={
                'verbose_name': '建物',
                'verbose_name_plural': '建物',
                'db_table': 'buildings',
            },
        ),

        # ── T-04 設備マスタ ──────────────────────────────────────
        migrations.CreateModel(
            name='Facility',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='設備名称')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='作成日時')),
            ],
            options={
                'verbose_name': '設備',
                'verbose_name_plural': '設備',
                'db_table': 'facilities',
            },
        ),

        # ── T-05 rooms テーブルへのリネーム ─────────────────────
        migrations.AlterModelTable(
            name='room',
            table='rooms',
        ),

        # ── 旧 building CharField を削除 ─────────────────────────
        migrations.RemoveField(
            model_name='room',
            name='building',
        ),

        # ── 新 building FK(Building) を追加 ──────────────────────
        migrations.AddField(
            model_name='room',
            name='building',
            field=models.ForeignKey(
                blank=True,
                db_column='building_id',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='rooms',
                to='reservations.building',
                verbose_name='建物',
            ),
        ),

        # ── T-06 会議室設備中間テーブル ──────────────────────────
        migrations.CreateModel(
            name='RoomFacility',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room', models.ForeignKey(
                    db_column='room_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='reservations.room',
                    verbose_name='会議室',
                )),
                ('facility', models.ForeignKey(
                    db_column='facility_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='reservations.facility',
                    verbose_name='設備',
                )),
            ],
            options={
                'verbose_name': '会議室設備',
                'verbose_name_plural': '会議室設備',
                'db_table': 'room_facilities',
            },
        ),
        migrations.AlterUniqueTogether(
            name='roomfacility',
            unique_together={('room', 'facility')},
        ),

        # ── T-07 所属別会議室テーブル ────────────────────────────
        migrations.CreateModel(
            name='DepartmentRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.ForeignKey(
                    db_column='department_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='accounts.department',
                    verbose_name='所属',
                )),
                ('room', models.ForeignKey(
                    db_column='room_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    to='reservations.room',
                    verbose_name='会議室',
                )),
            ],
            options={
                'verbose_name': '所属別会議室',
                'verbose_name_plural': '所属別会議室',
                'db_table': 'department_rooms',
            },
        ),
        migrations.AlterUniqueTogether(
            name='departmentroom',
            unique_together={('department', 'room')},
        ),

        # ── Reservation.room に related_name と verbose_name を追加 ──
        migrations.AlterField(
            model_name='reservation',
            name='room',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='reservations',
                to='reservations.room',
                verbose_name='会議室',
            ),
        ),
    ]
