/*
 * L.Control.GeoSearch - search for an address and zoom to it's location
 * https://github.com/smeijer/leaflet.control.geosearch
 */

L.GeoSearch = {};
L.GeoSearch.Provider = {};

// MSIE needs cors support
jQuery.support.cors = true;

L.GeoSearch.Result = function (x, y, label) {
    this.X = x;
    this.Y = y;
    this.Label = label;
};

L.AutoComplete = L.Class.extend({
    initialize: function (options) {
        this._config = {};
        L.Util.extend(this.options, options);
        this.setConfig(options);
    },

    setConfig: function (options) {
        var _this = this;
        this._config = {
            'maxSuggestions': options.maxSuggestions || 10,
            'onMakeSuggestionHTML': options.onMakeSuggestionHTML || function (geosearchResult) {
                return _this._htmlEscape(geosearchResult.Label);
            },
        };
    },

    addTo: function (container, onSelectionCallback) {
        this._container = container;
        this._onSelection = onSelectionCallback;
        return this._createUI(container, 'leaflet-geosearch-autocomplete');
    },

    _createUI: function (container, className) {
        this._tool = L.DomUtil.create('div', className, container);
        this._tool.style.display = 'none';
        var that = this;
        L.DomEvent
            .disableClickPropagation(this._tool)
            // consider whether to make delayed hide onBlur.
            // If so, consider canceling timer on mousewheel and mouseover.
            .on(this._tool, 'blur', this.hide, this) 
            .on(this._tool, 'mousewheel', function(e) {
                // TODO need to translate wheel motion to arrow up/down?
                L.DomEvent.stopPropagation(e); // to prevent map zoom
            }, this);
        return this;
    },


    show: function (results) {
        this._tool.innerHTML = '';
        this._tool.currentSelection = -1;
        var count = 0;
        while (count < results.length && count < this._config.maxSuggestions) {
            var entry = this._newSuggestion(results[count]);
            this._tool.appendChild(entry);
            ++count;
        }
        if (count > 0) {
            this._tool.style.display = 'block';
        } else {
            this.hide();
        }
        return count;
    },
    hide: function () {
        this._tool.style.display = 'none';
        this._tool.innerHTML = '';
    },

    isVisible: function() {
        return this._tool.style.display !== 'none';
    },

    _htmlEscape: function (str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    },

    _newSuggestion: function (result) {
        var tip = L.DomUtil.create('a', '');
        tip.href = '#';
        tip.innerHTML = this._config.onMakeSuggestionHTML(result);
        tip._text = result.Label;
        L.DomUtil.addClass(tip, 'leaflet-geosearch-suggestion'); //for styling
        var _this = this;
        L.DomEvent
            .disableClickPropagation(tip)
            .on(tip, 'click', L.DomEvent.stop, this) // from search plugin. why necessary? why separate?
            .on(tip, 'click', function(e) {
                _this._onSelection(tip._text);
            }, this);
        return tip;
    },
    _onSelectedUpdate: function () {
        var entries = this._tool.hasChildNodes() ? this._tool.childNodes : [];
        for (var ii=0; ii < entries.length; ++ii) {
            L.DomUtil.removeClass(entries[ii], 'leaflet-geosearch-suggestion-selected');
        }

        // if selection is -1, then show last user typed text
        if (this._tool.currentSelection >= 0) {
            L.DomUtil.addClass(entries[this._tool.currentSelection], 'leaflet-geosearch-suggestion-selected');

            // scroll:
            var tipOffsetTop = entries[this._tool.currentSelection].offsetTop;
            if (tipOffsetTop + entries[this._tool.currentSelection].clientHeight >= this._tool.scrollTop + this._tool.clientHeight) {
                this._tool.scrollTop = tipOffsetTop - this._tool.clientHeight + entries[this._tool.currentSelection].clientHeight;
            }
            else if (tipOffsetTop <= this._tool.scrollTop) {
                this._tool.scrollTop = tipOffsetTop;
            }

            this._onSelection(entries[this._tool.currentSelection]._text);
        } else {
            this._onSelection(this._lastUserInput);
        }
    },
    moveUp: function () {
        // permit selection to decrement down to -1 (none selected)
        if (this.isVisible() && this._tool.currentSelection >= 0) {
            --this._tool.currentSelection;
            this._onSelectedUpdate();
        }
        return this;
    },
    moveDown: function () {
        if (this.isVisible()) {
            this._tool.currentSelection = (this._tool.currentSelection + 1) % this.suggestionCount();
            this._onSelectedUpdate();
        }
        return this;
    },
    suggestionCount: function () {
        return this._tool.hasChildNodes() ? this._tool.childNodes.length : 0;
    },
});

L.Control.GeoSearch = L.Control.extend({
    options: {
        position: 'topcenter'
    },

    initialize: function (options) {
        this._config = {};
        L.Util.extend(this.options, options);
        this.setConfig(options);
    },

    setConfig: function (options) {
        this._config = {
            'country': options.country || '',
            'provider': options.provider,
            
            'searchLabel': options.searchLabel || 'search for address...',
            'notFoundMessage' : options.notFoundMessage || 'Sorry, that address could not be found.',
            'messageHideDelay': options.messageHideDelay || 3000,
            'zoomLevel': options.zoomLevel || 18,

            'maxMarkers': options.maxMarkers || 1
        };
    },

    onAdd: function (map) {
        var $controlContainer = $(map._controlContainer);

        if ($controlContainer.children('.leaflet-top.leaflet-center').length == 0) {
            $controlContainer.append('<div class="leaflet-top leaflet-center"></div>');
            map._controlCorners.topcenter = $controlContainer.children('.leaflet-top.leaflet-center').first()[0];
        }

        this._map = map;
        this._container = L.DomUtil.create('div', 'leaflet-control-geosearch');

        var searchbox = document.createElement('input');
        searchbox.id = 'leaflet-control-geosearch-qry';
        searchbox.type = 'text';
        searchbox.placeholder = this._config.searchLabel;
        this._searchbox = searchbox;
        this._lastUserInput = '';

        var _this = this;
        this._autocomplete = new L.AutoComplete({}).addTo(this._container, function (suggestionText) {
            _this._searchbox.value = suggestionText;
        });

        var msgbox = document.createElement('div');
        msgbox.id = 'leaflet-control-geosearch-msg';
        msgbox.className = 'leaflet-control-geosearch-msg';
        this._msgbox = msgbox;

        var resultslist = document.createElement('ul');
        resultslist.id = 'leaflet-control-geosearch-results';
        this._resultslist = resultslist;

        $(this._msgbox).append(this._resultslist);
        $(this._container).append(this._searchbox, this._msgbox, this._autocomplete);

        L.DomEvent
          .addListener(this._container, 'click', L.DomEvent.stop)
          .addListener(this._container, 'keypress', this._onKeyUp, this);

        L.DomEvent.disableClickPropagation(this._container);

        return this._container;
    },
    
    geosearch: function (qry) {
        var _this = this;
        var onSuccess = function(results) {
            _this._processResults(results);
        };
        var onFailure = function(error) {
            _this._printError(error);
        };
        this.geosearch_ext(qry, onSuccess, onFailure);
    },

    geosearch_ext: function(qry, onSuccess, onFailure) {
        try {
            var provider = this._config.provider;

            if(typeof provider.GetLocations == 'function') {
                var results = provider.GetLocations(qry, function(results) {
                    onSuccess(results);
                }.bind(this));
            }
            else {
                var url = provider.GetServiceUrl(qry);

                $.getJSON(url, function (data) {
                    try {
                        var results = provider.ParseJSON(data);
                        onSuccess(results);
                    }
                    catch (error) {
                        onFailure(error);
                    }
                }.bind(this));
            }
        }
        catch (error) {
            onFailure(error);
        }
    },

    geosearch_autocomplete: function (qry, request_delay_ms) {
        clearTimeout(this._autocomplete_request_timer);

        var _this = this;

        // local func rather than passing show func directly so correct context gets passed to show.
        var onSuccess = function(results) {
            _this._autocomplete.show(results);
        }

        var onFailure = function(error) {
            console.debug(error); 
            _this._autocomplete.hide();
        };

        this._autocomplete_request_timer = setTimeout(function () {
            _this.geosearch_ext(qry, onSuccess, onFailure);
        }, request_delay_ms);
    },

    _processResults: function(results) {
        if (results.length == 0)
            throw this._config.notFoundMessage;

        this._map.fireEvent('geosearch_foundlocations', {Locations: results});
        this._showLocations(results);
    },

    _showLocations: function (results) {
        if (typeof this._layer != 'undefined') {
            this._map.removeLayer(this._layer);
            this._layer = null;
        }

        this._markerList = []
        for (var ii=0; ii < results.length && ii < this._config.maxMarkers; ii++) {
            var location = results[ii];
            var marker = L.marker([location.Y, location.X]).bindPopup(location.Label);
            this._markerList.push(marker);
        }
        this._layer = L.layerGroup(this._markerList).addTo(this._map);

        var firstLocation = results[0];
        this._map.setView([firstLocation.Y, firstLocation.X], this._config.zoomLevel, false);
        this._map.fireEvent('geosearch_showlocation', {Location: firstLocation});
    },

    _printError: function(message) {
        $(this._resultslist)
            .html('<li>'+message+'</li>')
            .fadeIn('slow').delay(this._config.messageHideDelay).fadeOut('slow',
                    function () { $(this).html(''); });
    },
    
    _onKeyUp: function (e) {
        var REQ_DELAY_MS = 800;
        var MIN_AUTOCOMPLETE_LEN = 3;
        var escapeKey = 27;
        var enterKey = 13;
        var leftArrow = 37;
        var upArrow = 38;
        var rightArrow = 39;
        var downArrow = 40;
        var shift = 16;
        var ctrl = 17;

        switch (e.keyCode) {
            case escapeKey:
                if (this._autocomplete.isVisible()) {
                    this._autocomplete.hide();
                } else {
                    $('#leaflet-control-geosearch-qry').val('');
                    $(this._map._container).focus();
                }
                break;
            case enterKey:
                this.geosearch($('#leaflet-control-geosearch-qry').val());
                this._autocomplete.hide();
                break;
            case upArrow:
                if (this._autocomplete.isVisible()) {
                    this._autocomplete.moveUp();
                }
                break;
            case downArrow:
                if (this._autocomplete.isVisible()) {
                    this._autocomplete.moveDown();
                }
                break;
            case leftArrow:
            case rightArrow:
            case shift:
            case ctrl:
                break;
            default:
                var qry = $('#leaflet-control-geosearch-qry').val();
                if (qry !== 'undefined') {
                    this._lastUserInput = qry;
                }
                if (qry.length >= MIN_AUTOCOMPLETE_LEN) {
                    this.geosearch_autocomplete(qry, REQ_DELAY_MS);
                } else {
                    this._autocomplete.hide();
                }
        }
    }
});
