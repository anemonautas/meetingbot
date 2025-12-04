
FIND_AND_CLICK_JS = """
    var searchTextOptions = arguments[0];
    var tag = arguments[1];
    var doClick = arguments[2];

    function isVisible(elem) {
        return !!( elem.offsetWidth || elem.offsetHeight || elem.getClientRects().length );
    }

    function searchInDocument(doc) {
        var elements = doc.querySelectorAll(tag);
        for (var i = 0; i < elements.length; i++) {
            var el = elements[i];
            if (!isVisible(el)) continue;

            var text = (el.innerText || el.textContent || "").toLowerCase().trim();
            var aria = (el.getAttribute('aria-label') || "").toLowerCase();
            
            for (var j = 0; j < searchTextOptions.length; j++) {
                var opt = searchTextOptions[j].toLowerCase();
                if (text === opt || text.includes(opt) || aria === opt || aria.includes(opt)) {
                    return el;
                }
            }
        }
        
        var iframes = doc.querySelectorAll('iframe');
        for (var i = 0; i < iframes.length; i++) {
            try {
                var innerDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                if (innerDoc) {
                    var result = searchInDocument(innerDoc);
                    if (result) return result;
                }
            } catch(e) {}
        }
        return null;
    }

    var found = searchInDocument(document);
    if (found) {
        if (doClick) { 
            found.click(); 
            return "clicked"; 
        }
        return "found";
    }
    return null;
"""

FILL_INPUT_JS = """
    var value = arguments[0];
    var searchTerms = arguments[1] || [];

    var lowerSearchTerms = searchTerms.map(function(term) {
        return (term || "").toLowerCase();
    });

    function searchInput(doc) {
        if (!doc) return false;

        var inputs = doc.querySelectorAll("input");
        for (var i = 0; i < inputs.length; i++) {
            var el = inputs[i];
            var placeholder = (el.placeholder || "").toLowerCase();
            var aria = (el.getAttribute('aria-label') || "").toLowerCase();
            var nameAttr = (el.getAttribute('name') || "").toLowerCase();

            var match = lowerSearchTerms.some(function(term) {
                return placeholder.indexOf(term) !== -1 ||
                       aria.indexOf(term) !== -1 ||
                       nameAttr.indexOf(term) !== -1;
            });

            if (match) {
                el.focus();
                var setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, "value"
                );
                if (setter && setter.set) {
                    setter.set.call(el, value);
                } else {
                    el.value = value;
                }
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
                return true;
            }
        }

        var iframes = doc.querySelectorAll('iframe');
        for (var j = 0; j < iframes.length; j++) {
            try {
                var innerDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                if (innerDoc && searchInput(innerDoc)) return true;
            } catch(e) {}
        }
        return false;
    }
    return searchInput(document);
"""

CHECK_TEXT_PRESENCE_JS = """
    var rawSearchPhrases = arguments[0] || [];
    var searchPhrases = rawSearchPhrases.map(function(p) {
        return (p || "").toLowerCase();
    });

    function searchInDocument(doc) {
        if (!doc || !doc.body) return null;

        var bodyText = (doc.body.innerText || "").toLowerCase();
        for (var i = 0; i < searchPhrases.length; i++) {
            if (bodyText.indexOf(searchPhrases[i]) !== -1) {
                return rawSearchPhrases[i];
            }
        }

        var iframes = doc.querySelectorAll('iframe');
        for (var j = 0; j < iframes.length; j++) {
            try {
                var innerDoc = iframes[j].contentDocument || iframes[j].contentWindow.document;
                var found = searchInDocument(innerDoc);
                if (found) return found;
            } catch(e) {}
        }
        return null;
    }

    return searchInDocument(document);
"""
