; Declare skills to be added to the agent skills when workflow is loaded and
; removed on unloading workflow

(skill research-start "Create research project folders" (research_name_in_quotes topic_in_quotes))
(skill research-step "Mark research step done" (research_name_in_quotes step_in_quotes result_in_quotes next_action_in_quotes))
(skill research-checkpoint "Pause for user approval" (researchname_in_quotes message_in_quotes))
(skill research-complete "Finish research and unload workflow" (researchname_in_quotes))
(skill load-research-dynamic-instructions " Load a generated file into active context" (researchname_in_quotes filename_in_quotes))
(skill researchDir "Get research directory" ())

;; Actual skills implementation

;; Build a safe path or empty string if validation fails
(= (safe-instruction-path $project_dir $research-name $filename)
   (py-call (helper.safe_path (py-str ($project_dir)) (py-str ($research-name)) (py-str ($filename)))))

(= (load-research-dynamic-instructions  $research-name $filename)
    (let $d (researchDir) (load-dynamic-instructions $d $research-name $filename)))

; loads instructions created during workflow
(= (load-dynamic-instructions $project_dir $research-name $filename)
   (if (not (valid-file-or-folder-name $research-name))
       (send (py-str ("ERROR: invalid name: " $research-name)))
       (if (not (valid-file-or-folder-name $filename))
           (send (py-str ("ERROR: invalid filename: " $filename)))
           (let $path (safe-instruction-path $project_dir $research-name $filename)
                (if (== $path "")
                    (send (py-str ("ERROR: path traversal rejected for " $research-name "/" $filename)))
                    (load-dynamic-instructions-safe $path $research-name $filename))))))

; actually loads the file (internal). Only called after validation.
(= (load-dynamic-instructions-safe $path $research-name $filename)
   (if (not (exists-file $path))
       (send (py-str ("ERROR: file not found: " $path)))
       (let $content (read-file $path)
            (progn
              (change-state! &active_instructions $content)
              (appendToHistory ((get_time_as_string)
                                (newline)
                                (py-str ("LOADED [" $research-name "/" $filename "]"))
                                (newline)))
              (pin (py-str ("ACTIVE: " $research-name
                            " FILE: " $filename
                            " STATUS: executing"
                            " NEXT: follow loaded instructions")))
              (send (py-str ("Loaded " $filename " for " $research-name ". Following instructions.")))
              $content))))


(= (researchDir)
   ; FIXME: this directory should be created when workspace skill is loaded
   (let $dir (get-existing-dir (library memory/skills_workspace))
   (py-str ($dir "/research"))))


;; LLM decides to start research
;; creates folders for research and asks to create 00_problem.md then search online
(= (research-start $research-name $topic)
    (if (valid-file-or-folder-name $research-name)
       (progn (shell (py-str ("mkdir -p " (researchDir) "/" $research-name "/src")))
              (shell (py-str ("mkdir -p " (researchDir) "/" $research-name "/data")))
              (shell (py-str ("mkdir -p " (researchDir) "/" $research-name "/runs")))
              (shell (py-str ("mkdir -p " (researchDir) "/" $research-name "/figures")))
              (write-file (py-str ((researchDir) "/" $research-name "/topic.txt")) $topic)
              (send (py-str ("Created project: " (researchDir) "/" $research-name "\n"
                             "Folders: src/ data/ runs/ figures/")))
              (pin (py-str ("RESEARCH_ACTIVE: " $research-name
                            " DIR: " (researchDir) "/" $research-name
                            " TOPIC: " $topic
                            " STEP: 1-problem"
                            " ACTION_REQUIRED: Write 00_problem.md then search online"
                            " for related methods and data sources.")))
              $research-name)
        (send (py-str ("Invalid name: " $research-name ". Only a-z, 0-9, - and _ allowed.")))
       )
)

;; update current step
(= (research-step $research-name $step $result $next)
    (if (valid-file-or-folder-name $research-name)
       (progn (appendToHistory  ((get_time_as_string) (newline) (py-str  ("RESEARCH [" $research-name "] done: " $step " — " $result)) (newline)) )
              (send (py-str ("[" $research-name "] done: " $step)))
              (pin (py-str ("RESEARCH_ACTIVE: " $research-name
                            " DONE: " $step
                            " RESULT: " $result
                            " NEXT: " $next)))
              (py-str ("Done: " $step)))
        (send (py-str ("Invalid name: " $research-name ". Only a-z, 0-9, - and _ allowed.")))
     )
)


;; Checkpoint: wait user's response
(= (research-checkpoint $research-name $message)
    (if (valid-file-or-folder-name $research-name)
        (progn (pin (py-str ("RESEARCH_ACTIVE: " $research-name
                            " STATUS: WAITING_FOR_USER"
                            " DO_NOT_PROCEED"
                            )))
              (send (py-str ("CHECKPOINT [" $research-name "]\n" $message "\n"
                             "Reply to continue.")))
              "Waiting for user")
        (send (py-str ("Invalid name: " $research-name ". Only a-z, 0-9, - and _ allowed.")))
     )
)

;; Unload research skill
(= (research-complete $research-name)
    (if (valid-file-or-folder-name $research-name)
        (progn (change-state! &active_instructions "")
              (send (py-str ("Research complete: " $research-name
                             "\nResults in " (researchDir) "/" $research-name "/"
                             "\nWorkflow unloaded from context.")))
              (appendToHistory  ((get_time_as_string) (newline) (py-str  ("RESEARCH [" $research-name "] COMPLETED")) (newline)) )
              (pin "No active research. No active workflow.")
              "Research complete, workflow unloaded")
         (send (py-str ("Invalid name: " $research-name ". Only a-z, 0-9, - and _ allowed.")))
      )
)
