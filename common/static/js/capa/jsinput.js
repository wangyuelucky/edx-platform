(function () {

    // This function should only run once, even if there are multiple jsinputs
    // on a page.
    if (typeof(_jsinput_loaded) == 'undefined' || _jsinput_loaded === false) {
        _jsinput_loaded = true;
        setTimeout(walkDOM, 100);
    } else {
        return;
    }


    function jsinputConstructor (spec) {
        // Define an class that will be instantiated for each
        // jsinput element of the DOM

        // Private methods ----------------------------------------------------
        // Get the hidden input field to pass to customresponse
        function inputfield () {
            var parent = $(spec.elem).parent();
            return parent.find('input[id^="input_"]');
        }

        // Put the return value of gradefn in the hidden inputfield.
        function update () {
            var ans = $(spec.elem).
                    find('iframe[name^="iframe_"]').
                    get(0).      // jquery might not be available in the iframe
                    contentWindow.
                    gradefn();
            inputfield().val(ans);
            console.log("Answer: " + inputfield().val());
            return;
        }

        // Find the update button, and bind the update function to its click
        // event.
        function updateHandler () {
            var updatebutton = $(spec.elem).
                    find('button[class="update"]').get(0);

            $(updatebutton).click( update );
        }

        // Public methods -----------------------------------------------------
        // 'that' is the object returned by the constructor. It has a single
        // public method, "update", which updates the hidden input field.
        var that = {};
        that.update = update;

        updateHandler();

        return that;
    }

    function walkDOM () {
        // Find all jsinput elements, and create a jsinput object for each one
        var all = $(document).find('section[class="jsinput"]');
        var newid;
        all.each(function() {
            // Get just the mako variable 'id' from the id attribute
            newid = $(this).attr("id").replace(/^inputtype_/, "");
            var elem = this ;
            var newJsElem = jsinputConstructor({
                id: newid ,
                elem: this
            });
        });
    }


}).call(this);
