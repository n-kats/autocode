from abc import ABC, abstractmethod
from typing import Any, Type
from uuid import uuid4

from PIL import Image
from pydantic import BaseModel, Field


class WorkingState(BaseModel):
    used_ids: set[str] = Field(default_factory=set)
    current_scope_id: str | None = None
    scope_ids: set[str] = Field(default_factory=set)
    to_parent_scope_ids: dict[str, set[str]] = Field(default_factory=dict)
    to_sub_scope_ids: dict[str, set[str]] = Field(default_factory=dict)

    def generate_id(self, prefix: str | None = None) -> str:
        prefix = "" if prefix is None else prefix + "_"
        while True:
            new_id = f"{prefix}{uuid4().hex}"
            if new_id not in self.used_ids:
                break

        self.used_ids.add(new_id)
        return new_id

    def branch_scope(self, parent_scope_id: str, new_scope_id: str | None = None) -> str:
        new_scope_id = new_scope_id or self._new_scope_id()
        self.scope_ids.add(new_scope_id)
        self.to_parent_scope_ids.setdefault(new_scope_id, set()).add(parent_scope_id)
        self.to_sub_scope_ids.setdefault(parent_scope_id, set()).add(new_scope_id)
        return new_scope_id

    def root_scope(self) -> str:
        scope_id = self._new_scope_id()
        self.scope_ids.add(scope_id)
        self.current_scope_id = scope_id
        return scope_id

    def _new_scope_id(self) -> str:
        return self.generate_id(prefix="scope")


global_state = WorkingState()


class Entity(BaseModel):
    id_: str
    text: str | None
    image: str | None
    scope_id: str | None = None

    @classmethod
    def from_text(cls, text: str, state: WorkingState = global_state) -> "Entity":
        return cls(id_=state.generate_id(prefix="entity"), text=text, image=None, scope_id=state.current_scope_id)


class Context(BaseModel):
    entities: list[Entity] = Field(default_factory=list)
    is_active_entity: list[bool] = Field(default_factory=list)

    def add(self, entity: Entity | str, state: WorkingState = global_state) -> None:
        if isinstance(entity, Entity):
            self._add_entity(entity)
        elif isinstance(entity, str):
            self._add_entity(Entity.from_text(text=entity, state=state))
        else:
            raise ValueError("Unsupported entity type")

    def _add_entity(self, entity: Entity) -> None:
        self.entities.append(entity)
        self.is_active_entity.append(True)

    def copy(self) -> "Context":
        return Context(entities=self.entities.copy(), is_active_entity=self.is_active_entity.copy())

    def merge(self, other: "Context") -> "Context":
        existing_ids = {entity.id_ for entity in self.entities}
        new_entities = self.entities.copy()
        new_is_active = self.is_active_entity.copy()
        for entity, is_active in zip(other.entities, other.is_active_entity):
            if entity.id_ in existing_ids:
                continue
            new_entities.append(entity)
            new_is_active.append(is_active)
        return Context(entities=new_entities, is_active_entity=new_is_active)


class BaseCompressor(ABC):
    @abstractmethod
    def __call__(self, context: Context, state: WorkingState = global_state) -> Context:
        pass


class BaseWriter(ABC):
    @abstractmethod
    def __call__(self, text: str):
        pass

    @abstractmethod
    def plan(self, text: str, type_auto: str | None = None) -> Any:
        pass

    @abstractmethod
    def sub_writer(self, context: Context):
        pass

    @abstractmethod
    def add_context(self, context: Context, compressor: BaseCompressor):
        pass

    @abstractmethod
    def compress(self, compressor: BaseCompressor):
        pass


class BaseOutput(ABC):
    @abstractmethod
    def print(self, text: str) -> None:
        pass

    def __or__(self, other: "BaseOutput") -> "UnionOutput":
        return UnionOutput(self, other)


class UnionOutput(BaseOutput):
    def __init__(self, *outputs: BaseOutput):
        self.outputs = outputs

    def print(self, text: str) -> None:
        for output in self.outputs:
            output.print(text)


class LanguageModel(ABC):
    def __call__(self, prompt: str | list[str | Image.Image], output_structure: Type[BaseModel] | None = None) -> Any:
        """LLMを呼び出して、応答を取得します。"""
        pass
