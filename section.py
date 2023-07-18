class Section:
    def __init__(self, content, size):
        self.children = []
        self.size = size
        self.parent = None
        self.content = content

    def __eq__(self, other):
        if type(other) == str:
            return self.content.strip() == other
        if isinstance(other, self.__class__):
            return self.content.strip() == other.content.strip()
        return False

    def __repr__(self):
        return self.content

    def add_child(self, new_child):
        self.children.append(new_child)

    def has_child(self):
        return len(self.children) != 0

    def set_parent(self, new_parent):
        self.parent = new_parent

    def extend(self, content):
        self.content += f" {content}"

    def backtrack_add(self, content, size):
        curr = self

        while curr.size <= size:
            curr = curr.parent

        parent = curr
        cs = Section(content, size)
        parent.add_child(cs)
        cs.set_parent(parent)

        return cs

    def print_contents(self):
        if len(self.children) == 0:
            return self.content

        return (
            self.content
            + "\n"
            + " \n\n ".join([child.print_contents() for child in self.children])
        )
