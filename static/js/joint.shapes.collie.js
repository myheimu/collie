/*! JointJS v0.7.0 - JavaScript diagramming library  2013-11-04 


This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */
if (typeof exports === 'object') {

    var joint = {
        util: require('../src/core').util,
        shapes: {
            basic: require('./joint.shapes.basic')
        },
        dia: {
            ElementView: require('../src/joint.dia.element').ElementView,
            Link: require('../src/joint.dia.link').Link
        }
    };
    var _ = require('lodash');
}

joint.shapes.collie = {}

joint.shapes.collie.Data = joint.shapes.basic.Generic.extend({
    markup: [
        '<g class="rotatable">',
          '<g class="scalable">',
            '<rect class="collie-data-rect"/><ellipse class="collie-data-ellipse-top"/><ellipse class="collie-data-ellipse-bottom"/>',
          '</g>',
          '<text class="collie-data-name-text"/>',
        '</g>'
    ].join(''),
    
    defaults: joint.util.deepSupplement({
        type: 'collie.Data',
        attrs: {
            rect: { 'width': 130 },
            '.collie-data-rect': { 'stroke': 'black', 'stroke-width': 5, 'fill': '#ffffff', 'height': 160, 'transform': 'translate(8, 30)' },
            '.collie-data-ellipse-top': { 'stroke': 'black', 'stroke-width': 5, 'fill': '#ffffff', 'ry': 22, 'rx': 64, 'cy': 29, 'cx': 72 },
            '.collie-data-ellipse-bottom': { 'stroke': 'black', 'stroke-width': 5, 'fill': '#ffffff', 'ry': 22, 'rx': 64, 'cy': 189, 'cx': 72 },
            '.collie-data-name-text': {
                'ref': '.collie-data-rect', 'ref-y': .5, 'ref-x': .5, 'text-anchor': 'middle', 'y-alignment': 'middle', 'font-weight': 'bold',
                'fill': 'black', 'font-size': 12, 'font-family': 'Times New Roman'
            } 
        },
        node_id: []
    }, joint.shapes.basic.Generic.prototype.defaults),

    initialize: function() {
        _.bindAll(this, 'updateRectangles');
        this.on('change:name', function() {
            this.updateRectangles();
	    this.trigger('collie-update');
        });
        this.updateRectangles();
        joint.shapes.basic.Generic.prototype.initialize.apply(this, arguments);
    },

    getClassName: function() {
        return this.get('name');
    },

    updateRectangles: function() {
        var attrs = this.get('attrs');
        var rects = [
            { type: 'name', text: this.getClassName() }
        ];
        var offsetY = 0;
        _.each(rects, function(rect) {
            var lines = _.isArray(rect.text) ? rect.text : [rect.text];
	    var rectHeight = lines.length * 20 + 20;
            attrs['.collie-data-name-text'].text = lines.join('\n');
            attrs['.collie-data-rect'].height = 160;
            attrs['.collie-data-rect'].transform = 'translate(8, 30)';
            offsetY += rectHeight;
        });
    }
});

joint.shapes.collie.DataView = joint.dia.ElementView.extend({
    initialize: function() {
        joint.dia.ElementView.prototype.initialize.apply(this, arguments);
	this.model.on('collie-update', _.bind(function() {
	    this.update();
	    this.resize();
	}, this));
    }
});

joint.shapes.collie.Job = joint.shapes.basic.Generic.extend({
    markup: [
        '<g class="rotatable">',
          '<g class="scalable">',
            '<rect class="collie-job-name-rect"/><rect class="collie-job-attrs-rect"/>',
          '</g>',
          '<text class="collie-job-name-text"/><text class="collie-job-attrs-text"/>',
        '</g>'
    ].join(''),

    defaults: joint.util.deepSupplement({
        type: 'collie.Job',
        attrs: {
            rect: { 'width': 200 },
            '.collie-job-name-rect': { 'stroke': 'black', 'stroke-width': 2, 'fill': '#3498db' },
            '.collie-job-attrs-rect': { 'stroke': 'black', 'stroke-width': 2, 'fill': '#2980b9' },
            '.collie-job-name-text': {
                'ref': '.collie-job-name-rect', 'ref-y': .5, 'ref-x': .5, 'text-anchor': 'middle', 'y-alignment': 'middle', 'font-weight': 'bold',
                'fill': 'black', 'font-size': 12, 'font-family': 'Times New Roman'
            },
            '.collie-job-attrs-text': {
                'ref': '.collie-job-attrs-rect', 'ref-y': 5, 'ref-x': 5,
                'fill': 'black', 'font-size': 12, 'font-family': 'Times New Roman'
            }
        },
        name: [],
        attributes: [],
        node_id: []
    }, joint.shapes.basic.Generic.prototype.defaults),

    initialize: function() {
        _.bindAll(this, 'updateRectangles');
        this.on('change:name change:attributes', function() {
            this.updateRectangles();
	    this.trigger('collie-update');
        });
        this.updateRectangles();
        joint.shapes.basic.Generic.prototype.initialize.apply(this, arguments);
    },

    getClassName: function() {
        return this.get('name');
    },

    updateRectangles: function() {
        var attrs = this.get('attrs');
        var rects = [
            { type: 'name', text: this.getClassName() },
            { type: 'attrs', text: this.get('attributes') }
        ];
        var offsetY = 0;
        _.each(rects, function(rect) {
            var lines = _.isArray(rect.text) ? rect.text : [rect.text];
	    var rectHeight = lines.length * 20 + 20;
            attrs['.collie-job-' + rect.type + '-text'].text = lines.join('\n');
            attrs['.collie-job-' + rect.type + '-rect'].height = rectHeight;
            attrs['.collie-job-' + rect.type + '-rect'].transform = 'translate(0,'+ offsetY + ')';
            offsetY += rectHeight;
        });
    }
});

joint.shapes.collie.JobView = joint.dia.ElementView.extend({

    initialize: function() {

        joint.dia.ElementView.prototype.initialize.apply(this, arguments);

	this.model.on('collie-update', _.bind(function() {
	    this.update();
	    this.resize();
	}, this));
    }
});

joint.shapes.collie.Dependency = joint.dia.Link.extend({
    defaults: {
        type: 'collie.Dependency',
        attrs: { '.marker-target': { d: 'M 20 0 L 0 10 L 20 20 z', fill: 'white' }}
    }
});
