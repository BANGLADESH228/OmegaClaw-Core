(= (configure $name $default)
   (let $value (argk $name $default)
        (add-atom &self (= ($name) $value))))

