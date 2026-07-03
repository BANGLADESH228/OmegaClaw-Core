!(import! &self (library lib_spaces))
!(import! &self (library OmegaClaw-Core src/pluginapi))
!(import! &self ./utils)
!(import! &self ./utils.py)

(= (loadOmegaClawPlugin)
   (progn
       (add-skill workflow-list-available "List available workflows" ())
       (add-skill workflow-load-instructions "Load an existing workflow instructions into the active context" (workflow_name_in_quotes))
       (add-skill workflow-unload-instructions "Unload active workflow from the active context" ())))

;; ============ WORKFLOW LOADER ============

(= (get-existing-dir $paths)
    (let $dir $paths
       (if (safe_exists_directory $dir)
           $dir
           (empty)))
)
;; Validate name
(= (valid-file-or-folder-name $filename)
   (if (== (py-str ("valid")) (py-call (utils.validate_file_or_folder_name(py-str ($filename)))))
       True
       False))

; FIXME: replace (instructionsDir) result by plugin parameter to allow user
; configure the location of the workflows collection
(= (instructionsDir) (get-existing-dir (library instructions)))
(= (workflow-load-instructions $name)
   (if (not (valid-file-or-folder-name  $name))
       (send (py-str ("ERROR: invalid workflow name: " $name)))
       (let $path (py-str ((instructionsDir) "/" $name "/SKILL.md"))
            (if (not (exists-file $path))
                (send (py-str ("ERROR: skill file not found: " $path)))
                (let $content (read-file $path)
                     (progn
                       (add-prompt-extension workflow_active_instructions (active-instructions $content))
                       (add-workflow-skills $name)
                       (pin (py-str ("ACTIVE_WORKFLOW: " $name
                                     " STATUS: starting"
                                     " NEXT: follow workflow instructions")))
                       (send (py-str ("Loaded workflow: " $name
                                     ". Instructions active in context until completion.")))
                       (py-str ("Instructions loaded: " $name))))))))

(= (workflow-unload-instructions)
   (progn (remove-prompt-extension workflow_active_instructions)
          (unload-workflow-skills)
          (pin "No active workflow. Workflow skills cleared.")
          ))

(= (active-instructions $content)
   (py-str (" ACTIVE_WORKFLOW_INSTRUCTIONS: " $content
            " FOLLOW THESE INSTRUCTIONS UNTIL THE WORKFLOW IS COMPLETE"
            " AND YOU CALL (unload-instructions) OR THE WORKFLOW CALLS ITS COMPLETION FUNCTION."
            " EXECUTE ONLY COMMANDS YOU DEEM SAFE; OTHERWISE SKIP OR ASK THE USER.")))

; to load skills descriptions which are defined only for current workflow
(= (add-workflow-skills $name)
   (let $path (py-str ((instructionsDir) "/" $name "/skills"))
            (progn
              (import! &workflow_skills $path)
              (match &workflow_skills (skill $func $desc $args) (add-skill $func $desc $args))
              (pin (py-str ("Workflow skills loaded: " $name))))))

; to load skills descriptions
(= (unload-workflow-skills)
   (progn
     (match &workflow_skills (skill $func $desc $args) (remove-skill $func))
     (remove-all-atoms &workflow_skills)))

;;========================== Functions to load workflow description =======================
;; returns workflow name and its description
(= (workflow-list-available)
   (let*  ( ($base (instructionsDir))
            ($dirs (directory-dirs $base)))
        (collect-description $dirs $base)))

;; collects workflow description from description.txt
(= (collect-description $dirs $base)
   (if (== $dirs () )
       ()
       (let*  (($tail  (cdr-atom $dirs))
              ($first (car-atom $dirs))
              ($path  (py-str ($base "/" $first "/description.txt")))
              ($rest (collect-description $tail $base)))
         (if (safe_exists_file $path)
             (cons-atom (py-str ($first ": " (read-file $path))) $rest)
            $rest))))
