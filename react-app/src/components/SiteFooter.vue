<template>
    <v-footer color="transparent" class="footer py-1">
        <v-row justify="center" class="w-100" no-gutters>
            <v-col cols="12" class="text-center pa-0">
                <div class="footer-content">
                    <span class="footer-title"
                        ><strong>UQ Grade Calculator</strong> by
                        <a
                            href="https://github.com/Uncle-Mitch/uqmarks"
                            target="_blank"
                            rel="noopener"
                            class="footer-link"
                            >UncleMitch</a
                        >.
                    </span>
                    <br />
                    <span>
                        <a
                            href="https://github.com/Uncle-Mitch/uqmarks"
                            target="_blank"
                            rel="noopener"
                            class="footer-link"
                            >GitHub Link</a
                        >
                        &nbsp;|&nbsp;
                        <a
                            href="https://github.com/Uncle-Mitch/uqmarks/issues"
                            target="_blank"
                            rel="noopener"
                            class="footer-link"
                            >Report Issues</a
                        >
                    </span>
                    <br />
                    <span>
                        Inspired by
                        <a href="https://uqfinal.com/" target="_blank" rel="noopener" class="footer-link">UQfinal</a>
                    </span>
                </div>
            </v-col>
        </v-row>
    </v-footer>
</template>

<style scoped>
.footer {
    font-size: 0.75rem;
    color: white;
}

strong {
    font-weight: bold;
}

.footer-link {
    color: white;
    text-decoration: underline;
}
.footer-link:hover {
    color: #e3b3ff;
}
.footer-title {
    color: white;
}
</style>
