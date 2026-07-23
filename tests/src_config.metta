!(import! &self ./lib/utils.py)
!(import! &self ../src/config.py)
!(import! &self ./src/config)

(= (cleanup)
   (progn
     (match &self (= (command-line) $b) (remove-atom &self (= (command-line) $b)))))

; empty configuration

(= (command-line)
   ("config=./tests/res/src_config_empty.yaml"
    "arg_cmdline=val_cmdline"))
!(initConfig)

!(test (configGetByKey arg_config val_default) val_default)
!(test (configGetByKey arg_cmdline val_default) val_cmdline)
!(test (configGetByKey arg_notexist val_default) val_default)

!(cleanup)

; filled configuration

(= (command-line)
   ("config=./tests/res/src_config_filled.yaml"
    "arg_cmdline=val_cmdline"))
!(initConfig)

!(test (configGetByKey arg_config val_default) val_config)
!(test (configGetByKey arg_cmdline val_default) val_cmdline)
!(test (configGetByKey arg_notexist val_default) val_default)

!(configure arg_notexist val_default)
!(configure arg_config val_default)
!(configure arg_cmdline val_default)

!(test (arg_notexist) val_default)
!(test (arg_config) val_config)
!(test (arg_cmdline) val_cmdline)

!(cleanup)

; priorities configuration

(= (command-line)
   ("config=./tests/res/src_config_priorities.yaml"
    "arg_cmdline=val_cmdline"))
!(initConfig)

!(test (configGetByKey arg_cmdline val_default) val_cmdline)
!(test (configGetByKey arg_config val_default) val_config)
!(test (configGetByKey arg_notexist val_default) val_default)
