import bpy

# Every object created for a scene is linked under this collection, so the
# scene can be cleared (and saved) without touching the leaf and ground libraries.
RENDERS_COLLECTION = "renders"

# Custom property written on every scene object; the mask render uses it to
# decide which objects are plant (white) and which are ground (black).
ROLE_PROPERTY = "agrisyn_role"


class Builder:
    """Base of every scene element. Each builder owns one sub-collection of "renders"."""

    role = None  # "ground" or "plant"

    def __init__(self):
        self.root_collection = bpy.data.collections.get(RENDERS_COLLECTION)
        if self.root_collection is None:
            self.root_collection = bpy.data.collections.new(RENDERS_COLLECTION)
            bpy.context.scene.collection.children.link(self.root_collection)
        base_name = self.__class__.__name__.replace("Builder", "").lower()
        self.target_collection = self._new_collection(base_name)

    def _new_collection(self, base_name: str):
        name, counter = base_name, 1
        while bpy.data.collections.get(name) is not None:
            name = f"{base_name}_{counter:02d}"
            counter += 1
        collection = bpy.data.collections.new(name)
        self.root_collection.children.link(collection)
        return collection

    def link(self, obj) -> None:
        """Links `obj` to this builder's collection and tags it with the builder's role."""
        if self.target_collection not in obj.users_collection:
            self.target_collection.objects.link(obj)
        obj[ROLE_PROPERTY] = self.role

    def build(self) -> None:
        raise NotImplementedError
