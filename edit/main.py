from .app import EditorApplication


def main(use_tab: bool = False, tab_size: int = 2):
    app = EditorApplication(
        use_tab=use_tab,
        tab_size=tab_size,
    )

    app.run()


if __name__ == "__main__":
    main()