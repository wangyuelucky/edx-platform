(function () {

    console.log("Initialization");
    // This function should only run once, even if there are multiple jsinputs
    // on a page.
    if (typeof(_jsinput_loaded) == 'undefined' || _jsinput_loaded === false) {
        _jsinput_loaded = true;
        setTimeout(walkDOM, 100);
    } else {
        return;
    }


    function jsinputConstructor (spec) {
        // Define an class that will be instantiated for each.jsinput element
        // of the DOM

        /*                      Private methods                          */

        // Get the hidden input field to pass to customresponse
        function inputfield () {
            var parent = $(spec.elem).parent();
            return parent.find('input[id^="input_"]');
        }

        // Put the return value of gradefn in the hidden inputfield.
        // If passed an argument, does not call gradefn, and instead directly
        // updates the inputfield with the passed value.
        function update () {
            var ans;
            if ( arguments.length > 1) {
                console.log("Directly updating input field.");
                ans = arguments[1];
            } else {
                console.log("Calling gradefn to update input field.");
                ans = $(spec.elem).
                    find('iframe[name^="iframe_"]').
                    get(0).      // jquery might not be available in the iframe
                    contentWindow.
                    gradefn();
            }
            inputfield().val(ans);
            console.log("Answer:" + typeof(ans));
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


        /*                       Public methods                     */

        // 'that' is the object returned by the constructor. It has a single
        // public method, "update", which updates the hidden input field.
        var that = {};
        that.update = update;

        /*                      Initialization                          */
        
        if (spec.passive === false) {
            updateHandler();
        } else {
            // If set up to passively receive updates (intercept a function's
            // return value whenever the function is called) add an event
            // listener that listens to messages that match "that"'s id.
            // Decorate the iframe gradefn with updateDecorator.
            iframe.contentWindow[gradefn] = updateDecorator(iframe.contentWindow[gradefn]);
            iframe.contentWindow.addEventListener('message', function (e) {
                var id = e.data[0];
                var msg = e.data[1];
                if (id == spec.id) { update(msg); }
            });
        }

        return that;
    }

    function updateDecorator (fn, id) {
    // Simple function decorator that posts the output of a function to the
    // parent iframe before returning the original function's value.
    // Can be used to decorate one or more gradefn (instead of using an
    // explicit "Update" button) when gradefn is automatically called as part
    // of an application's natural behavior.
    // The id argument is used to specify which of the instances of jsinput on
    // the parent page the message is being posted to.
        return function () {
            var result = fn.apply(null, arguments);
            window.parent.contentWindow.postMessage([id, result], document.referrer);
            return result;
        };
    }

    function walkDOM () {
    // Find all jsinput elements, and create a jsinput object for each one
        var all = $(document).find('section[class="jsinput"]');
        var newid;
        all.each(function() {
            // Get just the mako variable 'id' from the id attribute
            newid = $(this).attr("id").replace(/^inputtype_/, "");
            console.log(newid);
            var elem = this ;
            var newJsElem = jsinputConstructor({
                id: newid ,
                elem: this ,
                passive: false 
            });
        });
    }

    var iframeInjection = {
        injectStyles : function (style) {
            $(document.body).css(style);
        },
        sendMySize : function () {
            var height = html.height;
            var width = html.width;
            window.parent.postMessage(['height', height], '*');
            window.parent.postMessage(['width', width], '*');
        }
    }

}).call(this);
