; Add skill to the list of skills available to the agent.
; $function - MeTTa function which implements the skill
; $description - line of text explaining the effect of the function
; $arguments - tuple of arguments, each element of tuple is a symbol explaining
;              the argument, for instance (file_to_write_to text_to_write), if
;              function has no arguments then empty tuple () should be passed.
(= (add-skill $function $description $arguments)
   (add-atom &self (= (dynamic-skill $function)
                      (py-str ("- " $description ": " $function " " (join " " $arguments))))))

; Remove skill from the list of skills available to the agent.
; $function - MeTTa function which implements the skill
(= (remove-skill $function)
   (match &self (= (dynamic-skill $function) $text) (remove-atom &self (= (dynamic-skill $function) $text))))

; Add new section to the LLM's prompt. The extension is inserted into the
; prompt after SKILL section and before OUTPUT_FORMAT section.
; $handle - symbol to identify and remove the section
; $text - text to add into the prompt
(= (add-prompt-extension $handle $text)
   (add-atom &self (= (prompt-extension $handle) $text)))

; Remove section from the LLM's prompt.
; $handle - symbol to identify the section
(= (remove-prompt-extension $handle)
   (match &self (= (prompt-extension $handle) $text) (remove-atom &self (= (prompt-extension $handle) $text))))

; FIXME: add MeTTa API to add communication channels and LLM integrations
