<global />

<template>
    <div class="header">
        <nav class="navbar navbar-inverse">
            <div class="navbar-header">
                <a class="navbar-brand" href="/">Standup</a>
            </div>
            <ul class="nav navbar-nav">
                <li v-for="project in projectSubset" class="dropdown">
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button">{{ project.name }} <span class="caret"></span></a>
                    <ul class="dropdown-menu">
                        <template v-for="board in project.boards">
                            <li v-for="sprint in board.sprints"><a v-bind:href="'/sprint/' + sprint.id">{{ sprint.name }} ({{ sprint.startDate }} - {{ sprint.endDate}})</a></li>
                        </template>
                        <li v-if="project.boards.filter(board => board.sprints.length > 0).length > 0" role="separator" class="divider"></li>
                        <template v-for="board in project.boards">
                            <li><a v-bind:href="$global.jiraUrl + '/secure/RapidBoard.jspa?view=planning&rapidView=' + board.id">Jira <b>{{ board.name }}</b> backlog</a></li>
                            <li><a v-bind:href="$global.jiraUrl + '/secure/RapidBoard.jspa?view=detail&rapidView=' + board.id">Jira <b>{{ board.name }}</b> sprints</a></li>
                        </template>
                    </ul>
                </li>
            </ul>
            <ul v-if="$global.user" class="nav navbar-nav navbar-right">
                <li><a href="/logout">Logout</a></li>
            </ul>
        </nav>
        <div v-if="$global.user" class="ident">
            <img v-bind:src="$global.user.avatar">
            <span>{{ $global.user.username }}</span>
        </div>
    </div>
</template>

<script>
    export default {
        props: ['projects'],
        computed: {
            projectSubset: function() {
                // Only include projects with boards, and only so many
                return this.projects ? this.projects.filter(project => project.boards.length > 0).slice(0, 4) : undefined;
            }
        }
    }
</script>

<style type="less">
    .header {
        display: flex;
        height: 75px;
        padding: 5px;
        background-color: #0152a1;
        border-bottom: 5px solid #4c4c4c;
        vertical-align: middle;

        .navbar {
            flex: 1 0 auto;
            margin: auto auto;
            padding-right: 10px;
        }

        .ident {
            flex: 0 0 auto;
            margin: 0 5px 0 10px;
            color: #fff;

            img {
                display: block;
                margin: 0 auto;
                height: 44px;
            }

            span {
                display: block;
                text-align: center;
            }
        }
    }
</style>
