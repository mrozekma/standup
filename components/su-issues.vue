<template>
    <table class="issues">
        <tr>
            <th></th>
            <th></th>
            <th>Key</th>
            <!--<th></th>-->
            <th>Summary</th>
            <th>Assignee</th>
            <th>Hours</th>
        </tr>
        <tr v-for="(issue, idx) in issuesOrdered" :data-id="issue.id" class="issue" :class="[`status-category-${issue.status.category}`, {sprint: issue.inSprint}]">
            <td class="index"><span class="badge">{{ idx + 1 }}</span></td>
            <td class="status"><img :src="`/static/images/status-${issue.status.category}.png`" :title="issue.status.name"></td>
            <td class="key">{{ issue.key }}</td>
            <!--<td class="expander"></td>-->
            <td class="summary" :style="`padding-left: ${issue.indent * 30}px;`"><img :src="issue.type.icon" :title="issue.type.name" class="type"> {{ issue.summary }}</td>
            <td v-if="issue.assignee" class="assignee">
                <img :src="issue.assignee.avatar" class="avatar">
                <div class="username">{{ issue.assignee.username }}</div>
            </td>
            <td v-else class="assignee">
                Unassigned
            </td>
            <td class="hours">
                <div class="estimate">{{ formatSeconds(issue.estimate) }}</div>
                <div class="remaining">{{ formatSeconds(issue.remaining) }}</div>
                <button :data-test="issue" @click="() => foobar(issue)">Foobar</button>
            </td>
        </tr>
    </table>
</template>

<script>
    export default {
        props: ['issues', 'parents'],
        data: function() {
            var order = [];
            var awaitingPlacement = [];

            // Place all root elements and queue the rest
            for(let issue of this.issues) {
                issue = Object.assign({}, issue, {inSprint: true, indent: 0});
                (issue.parent ? awaitingPlacement : order).push(issue);
            }
            for(let issue of this.parents) {
                issue = Object.assign({}, issue, {inSprint: false, indent: 0});
                (issue.parent ? awaitingPlacement : order).push(issue);
            }

            // On first pass, place all elements just below root. Then the elements just below those. Keep looping until everything is placed
            while(awaitingPlacement.length > 0) {
                for(var i = 0; i < order.length; i++) {
                    var parent = order[i];
                    // console.log(i + ' -- ' + order + ' -- ' + awaitingPlacement);

                    // Split 'awaitingPlacement' into two lists:
                    var placeNow = [], stillWaiting = [];
                    awaitingPlacement.forEach(issue => ((issue['parent'] === parent.id) ? placeNow : stillWaiting).push(issue));

                    if(placeNow.length > 0) {
                        placeNow.forEach(issue => issue.indent = parent.indent + 1);
                        order.splice.apply(order, [i + 1, 0, ...placeNow]);
                        i += placeNow.length;
                        awaitingPlacement = stillWaiting;
                    }
                }
            }

            return {
                // issuesById: issuesById,
                issuesOrdered: order
            };
        },
        methods: {
            formatSeconds: function(seconds) {
                // var weeks = Math.floor(seconds / 60 / 60 / 8 / 5);
                // seconds -= weeks * 60 * 60 * 8 * 5;

                // var days = Math.floor(seconds / 60 / 60 / 8);
                // seconds -= days * 60 * 60 * 8;

                var hours = Math.floor(seconds / 60 / 60);
                seconds -= hours * 60 * 60;

                var minutes = Math.floor(seconds / 60);
                seconds -= minutes * 60;

                // seconds should be 0 at this point; if not discard the rest

                return [
                    // weeks ? weeks + 'w' : null,
                    // days ? days + 'd' : null,
                    hours ? hours + 'h' : null,
                    minutes ? minutes + 'm' : null,
                ].filter(x => x).join(' ');
            },
            foobar: function(x) {
                console.log(x);
                x.remaining += 1 * 60 * 60;
            }
        }
    }
</script>

<style type="less">
    .issues {
        width: 100%;
        border-spacing: 0;

        tr.issue {
            &:hover td {
                background-color: #d9edf7;
                border-color: #d9edf7;
            }

            &:not(.sprint) {
                opacity: .4;
            }

            &.status-category-indeterminate {
                .key, .summary {
                    font-weight: bold;
                }
            }

            /*
            &.status-category-done {
                // Strikethrough. https://stackoverflow.com/a/19670807/309308
                // Not sure I actually like how it looks
                td {
                    position: relative;
                }
                td:before {
                    content: " ";
                    position: absolute;
                    top: 50%;
                    left: 0;
                    border-bottom: 1px solid #111;
                    width: 100%;
                }
            }
            */

            td {
                white-space: nowrap;
                padding: 4px 1px;
            }

            .index {
                text-align: right;
                .badge {
                    background-color: #3a87ad;
                }
            }

            .index, .key, .assignee {
                padding-right: 10px;
            }

            .summary {
                width: 100%;
            }

            .assignee {
                img {
                    width: 16px;
                    margin-right: 3px;
                }
                div.username {
                    display: inline-block;
                }
            }

            .hours {
                .estimate, .remaining {
                    display: inline-block;
                }
            }
        }
    }

    /* // Don't think this can be done without subgrid support
    .issues {
        display: grid;
        grid-template-areas: "status key expander type summary assignee hours";
        grid-template-columns: max-content max-content max-content max-content auto max-content max-content;
        .issue {
            display: contents;
            margin-bottom: 10px;
            .status {
                grid-area: status;
            }
            .key {
                grid-area: key;
            }
            .expander {
                grid-area: expander;
            }
            .type {
                grid-area: type;
            }
            .summary {
                grid-area: summary;
            }
            .assignee {
                grid-area: assignee;
                img {
                    width: @icon-width;
                    margin-right: 3px;
                }
                div.username {
                    display: inline-block;
                }
            }
            .hours {
                grid-area: hours;
                .estimate {
                    display: inline-block;
                }
                .remaining {
                    display: inline-block;
                }
            }
        }
    }
    */
</style>