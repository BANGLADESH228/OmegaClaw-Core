; This file is MeTTa trampoline to the plugin.py file

!(import! &self (library OmegaClaw-Core ./src/plugin.py))

(= (initPlugins)
   (progn
       (collapse (loadPlugins (py-call (plugin.listPlugins))))
       ()))

(= (commChannelConfig $commchannel)
   (py-call (plugin.commChannelConfig $commchannel (py-call (plugin.commandLineToDict (command-line))))))

(= (commChannelReceive)
   (py-call (plugin.commChannelReceive)))

(= (commChannelSend $message)
   (py-call (plugin.commChannelSend $message)))

(= (llmProviderConfig $provider)
   (py-call (plugin.llmProviderConfig $provider (py-call (plugin.commandLineToDict (command-line))))))

(= (llmProviderChat $prompt $max_tokens $reasoning_mode)
   (py-call (plugin.llmProviderChat $prompt $max_tokens $reasoning_mode)))

; Plugin loader

(= (loadPlugins $list)
   (let* (($head (car-atom $list))
          ($tail (cdr-atom $list)))
     (progn
       (loadPlugin $head)
       (loadPlugins $tail))))

(= (loadPlugin (python $name $location))
   (py-call (plugin.loadPythonPlugin $name $location)))

(= (loadPlugin (metta $name $location))
   (let True (atom-string $location $locationstr)
       (loadMettaPlugin $name $locationstr)))

(= (loadMettaPlugin $name $location)
   (if (== $location "")
     (log ERROR "plugin" (strings-concat ("Plugin " $name " no location specified")))
     (progn
       (let $path (join "/" ($location $name)) ())
       (let $space (atom-concat & $name) ())
       (log INFO "plugin" (strings-concat ("Loading MeTTa plugin " $name " from " $path ".metta")))
       (if (empty-to-bool (import! $space $path))
         (progn
           ; FIXME: pass configuration to the plugin initialization function
           ; FIXME: fail if loadOmegaClawPlugin returns Error
           (eval (loadOmegaClawPlugin))
           (match $space (= (loadOmegaClawPlugin) $body) (remove-atom $space (= (loadOmegaClawPlugin) $body)))
           (log INFO "plugin" (strings-concat ("Plugin " $name " is loaded"))))
         (log ERROR "plugin" (strings-concat ("Plugin " $name " loading failed")))))))
