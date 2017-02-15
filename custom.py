
css_selectors = {
    'email_field': '#email',
    'password_field': '#pass',
    'login_form': '#login_form',

}


xpath_selectors = {
    'friends_selector': "//ul[contains(@data-pnref, 'friends')]//div[contains(@class, 'uiProfileBlockContent')]//a[@data-hovercard]",
    'likes_selector': "//div[contains(@id, 'pagelet_timeline_medley_likes')]//li//a[@data-hovercard and not(*)]",
}

page_references = {
    'friends_page': '&sk=friends',
    'likes_page': '&sk=likes',
}
