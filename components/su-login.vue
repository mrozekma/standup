<global />

<template>
    <su-callout type="danger" v-bind:title="title" class="su-login">
        {{ text }}<br><br>
        <a class="btn btn-primary jira" :href="loginUrl">{{ button }}</a>
    </su-callout>
</template>

<script>
    export default {
        props: {
            denied: { // True if Jira returned a denied token, false if the user hasn't tried yet
                type: Boolean,
                default: false
            }
        },
        computed: {
            title: function() {
                return !this.denied ? 'Login required' : 'Login failed';
            },
            text: function() {
                return !this.denied ? 'You must login with your Jira credentials to use Standup:' : 'Jira access denied';
            },
            button: function() {
                return !this.denied ? 'Login' : 'Try again';
            },
            loginUrl: function() {
                // Jira strips off one URL encoding
                return '/login?redir=' + encodeURIComponent(encodeURIComponent(window.location.pathname + window.location.hash));
            },
        }
    }
</script>