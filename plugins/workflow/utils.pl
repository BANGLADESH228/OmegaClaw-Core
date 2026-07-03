safe_exists_file(Path, true)       :- exists_file(Path), !.
safe_exists_file(_, false).


safe_exists_directory(Path, true)  :- exists_directory(Path), !.
safe_exists_directory(_, false).
