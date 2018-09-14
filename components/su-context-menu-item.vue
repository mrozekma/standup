<template>
    <li class="context-menu-item" @click="$emit('click')">
        <img :src="icon" :title="title">
        <div class="name">{{ text }}</div>
    </li>
</template>

<script>
    export default {
        props: ['icon', 'text', 'title'],
    }
</script>

<style type="less">
    .context-menu-item {
        img {
            width: 16px;
            margin-right: 3px;
        }
        div.name {
            display: inline-block;
        }
    }
</style>
