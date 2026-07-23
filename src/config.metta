(= (initConfig)
   (progn
     (py-call (config.init_config (command-line)))
     ()))

(= (configure $key $default)
   (let $value (configGetByKey $key $default)
     (add-atom &self (= ($key) $value))))

(= (configGetByKey $key $default)
   (py-call (config.config_get_by_key $key $default)))
