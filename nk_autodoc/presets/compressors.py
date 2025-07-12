from nk_autodoc.framework import Context, Entity, WorkingState, global_state


class Compressor:
    def __call__(self, context: Context, state: WorkingState = global_state) -> Context:
        if state.current_scope_id is None:
            target_scope_ids = state.scope_ids.copy()
        else:
            target_scope_ids = state.to_parent_scope_ids.get(state.current_scope_id, set()).copy()
            target_scope_ids.add(state.current_scope_id)
        valid_entities = [
            entity
            for entity, active in zip(context.entities, context.is_active_entity)
            if active and entity.scope_id in target_scope_ids
        ]
        new_entity = self._generate_compressed_entity(valid_entities, state)

        return Context(
            entities=context.entities + [new_entity], is_active_entity=[False] * len(context.entities) + [True]
        )

    def _generate_compressed_entity(self, entities: list[Entity], state: WorkingState) -> Entity:
        return Entity(
            id_=state.generate_id(prefix="compressed_entity"),
            text=" ".join(entity.text for entity in entities if entity.text),
            image=None,
            scope_id=state.current_scope_id,
        )
