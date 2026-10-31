# PerturbationConfig（扰动参数配置）—— 数据表定义
#
# ── 这个文件在链路中的位置 ──────────────────────────────────────────────
#   routers/v1/perturbations.py   只收参数、返回响应
#        ↓
#   services/perturbation_service.py   业务规则（项目是否存在、默认值、事务）
#        ↓
#   repositories/perturbation_repo.py  只写 SQL 查询
#        ↓
#   models/perturbation.py（本文件）   只描述"表长什么样"
#
# ── 设计约定 ────────────────────────────────────────────────────────────
# 1. 一个项目一份配置：project_id 加 unique 约束，天然防止重复行。
# 2. 开关可多选：每种扰动一个 Boolean 字段，字段名与前端
#    store/perturbation.js 里的 PERTURBATION_OPTIONS[].key 完全一致，
#    这样前端可以把 store 里的对象直接 PUT 上来，不需要字段映射。
# 3. 预留两个参数列，后面做"扰动强度"时不用再改表结构：
#      params   -> JSON，默认 NULL，存放各扰动自己的参数
#                  （如 {"brightness_factor": 1.2}）
#      strength -> Integer，默认 100，统一的强度百分比
#    目前前端只提交三个开关，这两列不参与任何业务逻辑。
#
# ── 注意 ────────────────────────────────────────────────────────────────
# 新增/修改模型后，必须确保 app/models/__init__.py 里 import 了本类，
# 否则 Base.metadata.create_all 看不到这张表，启动时不会建表。
# 本项目目前用 create_all 而不是 Alembic，所以"加字段"对已有数据库
# 不会自动生效：开发阶段删掉 test_platform.db 重新启动即可。
from sqlalchemy import JSON, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import PKMixin, TimestampMixin


class PerturbationConfig(PKMixin, TimestampMixin, Base):
    """
    扰动参数配置表（表名 perturbation_configs）。

    继承关系：
    - PKMixin      提供 id 主键（自增）
    - TimestampMixin 提供 created_at / updated_at（updated_at 会在 UPDATE 时自动刷新）
    - Base         SQLAlchemy 2.0 声明式基类
    """

    __tablename__ = "perturbation_configs"

    # 配置归属的项目。
    # - ForeignKey("projects.id")：数据库层面保证 project_id 一定存在
    # - unique=True：一个项目只能有一行配置，避免并发下出现两份
    # - index=True：按项目查配置是最频繁的查询，加索引
    # 删除项目时由 ProjectService.delete 显式清理本表，
    # 不依赖数据库级联，这样已有数据库不需要重建表。
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"), unique=True, index=True
    )

    # 三个扰动开关。默认 False，与前端 DEFAULT_PERTURBATION_CONFIG 一致。
    # 注意：这里的 default 是 Python 端默认值，只在 INSERT 时生效；
    # 已有行不会因为改了 default 而变化。
    enable_brightness: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_contrast: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_noise: Mapped[bool] = mapped_column(Boolean, default=False)

    # 预留：各类扰动自己的参数。
    # SQLAlchemy 的 JSON 类型在 SQLite 里实际存成 TEXT，读写时自动做
    # dict <-> JSON 字符串的转换；nullable=True 表示允许 NULL（还没配置）。
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)

    # 预留：统一强度百分比，0-100，默认 100（即"满强度"）。
    # 校验范围放在 Pydantic schema 里（ge=0, le=100），模型层不加约束，
    # 避免以后放宽范围时还要改表。
    strength: Mapped[int] = mapped_column(Integer, default=100)

    # ── 以后可能的扩展 ──────────────────────────────────────────────────
    # 如果扰动种类会不断增多，可以把"一列一个开关"改成子表：
    # PerturbationItem(config_id, type, enabled, params)
    # 好处是加扰动类型不用改表结构；代价是查询和前端映射都更复杂。
    # 目前只有 3 种，先用宽表最简单，前端也能直接绑定字段。
