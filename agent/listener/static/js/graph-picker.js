var GRAPHABLES = [
    'disk',
    'interface',
    'memory',
    'cpu'
];

function remove_selects_below(e) {
    var current = $(e.target);
    var parent = current.closest('form');

    parent.nextAll().remove();
}

function get_next_select(api_address, selection) {
    var select = $('<select>', {'data-children': api_address});

    $.getJSON(api_address, function(d) {
        var element = d.value[selection];
        var bind_graph = false;
        $.each(element, function(k, v) {

            // This is a special case for when we are in the root node
            // and we target a node that has no graphable children.
            if (selection == 'root' && GRAPHABLES.indexOf(k) == -1) {
                return;
            }

            select.append($('<option>', {value: k, text: k, 'data-children': k}));

            if (element[k] instanceof Array) {
                select.attr('id', 'graph-bringer');
                bind_graph = true;
            }
        });

        if (bind_graph) {
            select.change(function(e) {
                render_graph($(e.target));
            });
        }
        else {
            select.change(function(e) {
                remove_selects_below(e);
                populate_next_select(e);
            })
        }

        select.trigger('change');
    });

    return select;
}

function wrap_select_in_form(select) {
    var form = $('<form>', {class: 'form-inline graph-picker-holder'});
    var label = $('<label>', {class: 'control-label centered'});
    label.append(select);
    form.append(label);
    return form;
}

function get_graph_url(api_url) {
    if (api_url == undefined) {
        var raw_api_url = $('#graph-address-url').val();
        api_url = raw_api_url.replace(/\?.*/g, '');
    }

    var graph_url = api_url.replace(/^\/api/g, '/graph');

    var delta = $('input[name=delta]:checked').val();
    var units = $('input[name=units]:checked').val();
    var unit = $('input[name=unit]').val();

    var query_args = {};

    if (delta == 'on') {
        query_args['delta'] = 1;
    }

    if (units != 'None') {
        query_args['units'] = units;
    }

    if (unit) {
        query_args['unit'] = unit;
    }

    var qs = $.param(query_args);
    return (qs) ? graph_url + '?' + qs : graph_url;
}

function render_graph(target) {
    var graph_content = $('#graph-content');
    var graph_url = '';
    var api_url = '';

    if (target == undefined) {
        graph_url = get_graph_url()
    }
    else {
        api_url = target.attr('data-children') + '/' + target.val();
        graph_url = get_graph_url(api_url);
    }

    $('#not-renderable').hide();
    $('#graph-address-url').val(graph_url);
    $('.ncpa-graph').trigger('doUnload');


    graph_content.empty();
    graph_content.load(graph_url);
}

function populate_next_select(e) {
    var current = $(e.target);
    var next_url = current.attr('data-children') + '/' + current_value;

    var next_select = get_next_select(next_url, current_value);
    var next_form = wrap_select_in_form(next_select);

    var closest_form = current.closest('form');
    closest_form.after(next_form);
}

function initialize() {
    var graph_selector_div = $('#graph-selector-div');
    var initial_select = get_next_select('/api', 'root');
    var initial_form = wrap_select_in_form(initial_select);

    graph_selector_div.append(initial_form);
}

$(document).ready(function() {
    initialize();

    $('#refresh-graph').click(function() {
        render_graph();
    });
});