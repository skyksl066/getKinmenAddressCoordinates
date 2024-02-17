(() => {
    'use strict'

    const getStoredTheme = () => localStorage.getItem('theme')
    const setStoredTheme = theme => localStorage.setItem('theme', theme)

    const getPreferredTheme = () => {
        const storedTheme = getStoredTheme()
        if (storedTheme) {
            return storedTheme
        }

        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }

    const setTheme = theme => {
        if (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-bs-theme', 'dark')
        } else {
            document.documentElement.setAttribute('data-bs-theme', theme)
        }
    }

    setTheme(getPreferredTheme())

    const showActiveTheme = (theme, focus = false) => {
        const themeSwitcher = document.querySelector('#bd-theme')

        if (!themeSwitcher) {
            return
        }

        const themeSwitcherText = document.querySelector('#bd-theme-text')
        const activeThemeIcon = document.querySelector('.theme-icon-active use')
        const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`)
        const svgOfActiveBtn = btnToActive.querySelector('svg use').getAttribute('href')

        document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
            element.classList.remove('active')
            element.setAttribute('aria-pressed', 'false')
        })

        btnToActive.classList.add('active')
        btnToActive.setAttribute('aria-pressed', 'true')
        activeThemeIcon.setAttribute('href', svgOfActiveBtn)
        const themeSwitcherLabel = `${themeSwitcherText.textContent} (${btnToActive.dataset.bsThemeValue})`
        themeSwitcher.setAttribute('aria-label', themeSwitcherLabel)

        if (focus) {
            themeSwitcher.focus()
        }
    }

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        const storedTheme = getStoredTheme()
        if (storedTheme !== 'light' && storedTheme !== 'dark') {
            setTheme(getPreferredTheme())
        }
    })

    window.addEventListener('DOMContentLoaded', () => {
        showActiveTheme(getPreferredTheme())

        document.querySelectorAll('[data-bs-theme-value]')
            .forEach(toggle => {
                toggle.addEventListener('click', () => {
                    const theme = toggle.getAttribute('data-bs-theme-value')
                    setStoredTheme(theme)
                    setTheme(theme)
                    showActiveTheme(theme, true)
                })
            })
    })

    let table = new DataTable('#my_table', {
        responsive: true,
        lengthChange: false,
        rowReorder: false,
        language: {
            searchPlaceholder: "Search",
            search: "",
        },
        ajax: {
            url: 'data/data.json',
            dataSrc: 'data'
        },
        columns: [
            {
                title: 'ADDR', data: 'ADDR',
                render: function (data, type, row, meta) {
                    if (type === 'display') {
                        let params = {
                            q: row['LATITUDE'] + ',' + row['LONGITUDE']
                        };
                        let url = "https://maps.google.com/?" + $.param(params, true);
                        return '<a href="' + url + '" target="_blank">' + data + '</a>';
                    }
                    return data;
                }
            },
            { title: 'LATITUDE', data: 'LATITUDE', visible: false },
            { title: 'LONGITUDE', data: 'LONGITUDE', visible: false },
            { title: 'TOWN', data: 'TOWN' },
            { title: 'ROAD', data: 'ROAD' },
            { title: 'LANE', data: 'LANE' },
            { title: 'ALLEY', data: 'ALLEY' },
            { title: 'DOOR', data: 'DOOR' }
        ],
        processing: true,
        initComplete: function (settings, json) {
            let info = settings.api.page.info();
            let width = $(document).width();
            if (width <= 767.98) {
                if (info.page == 0) {
                    $('.swiper-button-prev').hide();
                } else {
                    $('.swiper-button-prev').show();
                }
                if (info.page == info.pages - 1) {
                    $('.swiper-button-next').hide();
                } else {
                    $('.swiper-button-next').show();
                }
                $('#my_table_wrapper .dt-paging').hide();
            } else {
                $('#my_table_wrapper .dt-paging').show();
            }
            $('#my_table_wrapper .dt-search').addClass('form-group has-search');
            $(`<span class="form-control-feedback">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-search" viewBox="0 0 16 16">
                            <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0" />
                        </svg>
                    </span>`).insertBefore('#dt-search-0');
        }
    });

    $('.swiper-button-prev').on('click', () => {
        table.page('previous').draw(false);
    })

    $('.swiper-button-next').on('click', () => {
        table.page('next').draw(false);
    });

    table.on('page', () => {
        let info = table.page.info();
        let width = $(document).width();
        if (width <= 767.98) {
            if (info.page == 0) {
                $('.swiper-button-prev').hide();
            } else {
                $('.swiper-button-prev').show();
            }
            if (info.page == info.pages - 1) {
                $('.swiper-button-next').hide();
            } else {
                $('.swiper-button-next').show();
            }
            $('#my_table_wrapper .dt-paging').hide();
        } else {
            $('#my_table_wrapper .dt-paging').show();
        }
    });

    $(window).resize(() => {
        let info = table.page.info();
        let width = $(document).width();
        if (width <= 767.98) {
            if (info.page == 0) {
                $('.swiper-button-prev').hide();
            } else {
                $('.swiper-button-prev').show();
            }
            if (info.page == info.pages - 1) {
                $('.swiper-button-next').hide();
            } else {
                $('.swiper-button-next').show();
            }
            $('#my_table_wrapper .dt-paging').hide();
        } else {
            $('#my_table_wrapper .dt-paging').show();
        }
    });
})();