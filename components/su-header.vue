<global />

<template>
    <div class="header">
        <nav class="navbar navbar-inverse">
            <div class="navbar-header">
                <a class="navbar-brand" href="/">Standup</a>
            </div>
            <vue-simple-spinner v-if="$global.user && projects == null" size="medium" class="loading nav navbar-nav"></vue-simple-spinner>
            <ul v-if="$global.user" class="nav navbar-nav">
                <li v-for="project in projects" class="dropdown">
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button">{{ project.name }} <span class="caret"></span></a>
                    <ul class="dropdown-menu">
                        <template v-for="board in project.boards">
                            <li v-for="sprint in board.sprints"><a :href="`/sprint/${sprint.id}`">{{ sprint.name }} ({{ sprint.startDate }} - {{ sprint.endDate}})</a></li>
                        </template>
                        <li v-if="project.boards.filter(board => board.sprints.length > 0).length > 0" role="separator" class="divider"></li>
                        <li><a :href="`${$global.jiraUrl}/projects/${project.key}/summary`" class="jira">Project home</a></li>
                        <template v-for="board in project.boards">
                            <li><a :href="`${$global.jiraUrl}/secure/RapidBoard.jspa?view=planning&rapidView=${board.id}`" class="jira">{{ board.name }} backlog</a></li>
                            <li><a :href="`${$global.jiraUrl}/secure/RapidBoard.jspa?view=detail&rapidView=${board.id}`" class="jira">{{ board.name }} sprints</a></li>
                        </template>
                    </ul>
                </li>
            </ul>
            <ul v-if="$global.user" class="nav navbar-nav navbar-right">
                <li><a href="/logout">Logout</a></li>
            </ul>
            <ul class="nav navbar-nav navbar-right">
                <li><a href="/help">Help</a></li>
            </ul>
        </nav>
        <div v-if="$global.user" class="ident">
            <img :src="$global.user.avatar">
            <span>{{ $global.user.username }}</span>
        </div>
    </div>
</template>

<script>
    export default {
        data: function() {
            return {
                projects: null,
            };
        },
        mounted: function() {
            if(this.$global.user) {
                var self = this;
                $.get({
                    url: '/data?recent',
                    success: function(data) {
                        self.projects = data;
                    },
                    error: function(xhr, type, desc) {
                        console.error(type);
                        console.error(desc);
                        var error = (type == 'error') ? xhr.responseText : desc;
                        if(!error) {
                            error = 'Unknown error';
                        }
                        Vue.toasted.show(error, {
                            position: 'bottom-center',
                            duration: 5000,
                            icon: 'exclamation-circle',
                            type: 'error',
                            closeOnSwipe: true,
                        });
                    }
                })
            }
        },
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

            .loading {
                margin-top: 8px;
            }
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

        a.jira {
            padding-left: 40px;
            background-position-x: 20px;
        }
    }
</style>
