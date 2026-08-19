from .file_helpers import split_path

def get_result_render(path):
    def render_results(results, value, position, offset, width, n_rows=10):
        print(f"Found {len(results)} results in {path}:".ljust(width))

        for line in range(n_rows):
            index = offset + line

            if index < len(results):
                prefix = "> " if line == position else "  "
                dir_path, file_name = split_path(results[index])
                print(f"{prefix}{index}. {file_name} ({dir_path})"[:width].ljust(width))
            else:
                print(" " * width)
    return render_results
