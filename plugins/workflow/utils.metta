!(import_prolog_functions_from_file ./utils.pl (safe_exists_directory safe_exists_file))

( = (directory-files $dir)
   (progn (translatePredicate (directory_files $dir $files))
          $files)
)

( = (directory-dirs $dir)
  (let $f (directory-files $dir)
       (filter-dirs  $f $dir)
   )
)


(= (filter-dirs $files $dir)
   (if (== $files ())
       ()
       (progn (translatePredicate (atom_string (car-atom $files) $first))
               (let* (
                      ($tail     (cdr-atom $files))
                      ($fullpath (py-str ($dir "/" $first)))
                      ($rest     (filter-dirs $tail $dir)))
                         (if (or (== $first ".") (== $first ".."))
                             $rest
                             (if (safe_exists_directory $fullpath)
                                 (cons-atom $first $rest)
                                 $rest))
                 )
        )
    )
)
