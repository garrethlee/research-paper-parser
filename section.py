class Section:
    """
    Represents a section with content and size.

    Attributes:
        content (str): The content of the section.
        size (int): The size of the section.
        children (List[Section]): The list of child sections.
        parent (Section): The parent section.
    """

    def __init__(self, content: str, size: int):
        """
        Initialize a Section object.

        Args:
            content (str): The content of the section.
            size (int): The size of the section.
        """
        self.children = []
        self.size = size
        self.parent = None
        self.content = content

    def __eq__(self, other) -> bool:
        """
        Check if the current section is equal to another section or a string.

        Args:
            other (Union[str, Section]): The other section or string to compare.

        Returns:
            bool: True if the contents are equal; False otherwise.
        """
        if isinstance(other, str):
            return self.content.strip() == other
        if isinstance(other, self.__class__):
            return self.content.strip() == other.content.strip()
        return False

    def __repr__(self) -> str:
        """
        Return a string representation of the section.

        Returns:
            str: The content of the section.
        """
        return self.content

    def add_child(self, new_child: "Section") -> None:
        """
        Add a child section to the current section.

        Args:
            new_child (Section): The new child section to add.
        """
        self.children.append(new_child)

    def has_child(self) -> bool:
        """
        Check if the current section has children.

        Returns:
            bool: True if the section has children; False otherwise.
        """
        return len(self.children) != 0

    def set_parent(self, new_parent: "Section") -> None:
        """
        Set the parent of the current section.

        Args:
            new_parent (Section): The new parent section.
        """
        self.parent = new_parent

    def extend(self, content: str) -> None:
        """
        Extend the content of the section with additional content.

        Args:
            content (str): The content to add to the section.
        """
        self.content += f" {content}"

    def backtrack_add(self, content: str, size: int) -> "Section":
        """
        Add a new section to the parent section until the size constraint is met.

        Args:
            content (str): The content of the new section.
            size (int): The size of the new section.

        Returns:
            Section: The newly created section.
        """
        curr = self

        while curr.size <= size:
            curr = curr.parent

        parent = curr
        cs = Section(content, size)
        parent.add_child(cs)
        cs.set_parent(parent)

        return cs

    def print_contents(self) -> str:
        """
        Recursively print the contents of the section and its children.

        Returns:
            str: The formatted content of the section and its children.
        """
        if len(self.children) == 0:
            return self.content

        return (
            self.content
            + "\n"
            + " \n\n ".join([child.print_contents() for child in self.children])
        )
