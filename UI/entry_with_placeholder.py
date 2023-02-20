import tkinter as tk


class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey', highlightcolor="#feda5b", width=None,
                 font=None):
        super().__init__(master)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        self.config(highlightcolor=highlightcolor)
        if font is not None:
            self.config(font=font)

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

        if width is not None:
            self.config(width=width)

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()

    def insert_text(self, text):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color
            self.insert(0, text)

    def set_text(self, text):
        self.delete('0', 'end')
        self['fg'] = self.default_fg_color
        self.insert(0, text)

    def get_text(self):
        if self['fg'] == self.placeholder_color:
            return self.placeholder
        return self.get()


if __name__ == "__main__":
    root = tk.Tk()
    username = EntryWithPlaceholder(root, "username")
    password = EntryWithPlaceholder(root, "password", 'blue')
    username.pack()
    password.pack()
    root.mainloop()
