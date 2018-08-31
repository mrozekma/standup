<global />

<template>
    <div class="header">
        <nav class="navbar navbar-inverse">
            <div class="navbar-header">
                <a class="navbar-brand" href="/">Standup</a>
            </div>
            <ul class="nav navbar-nav">
                <li class="active"><a href="#">Foo</a></li>
                <li><a href="#">Bar</a></li>
                <li><a href="#">Baz</a></li>
                <li><a href="/logout">Qux</a></li>
            </ul>
        </nav>
        <div v-if="username" class="ident">
            <img v-bind:src="userAvatar">
            <span>{{ username }}</span>
        </div>
    </div>
</template>

<script>
    export default {
        props: ['username', 'userAvatar']
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
