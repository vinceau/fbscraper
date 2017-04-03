"""
AIM

we want to do something like this:

find the people named kim who has visited seoul
search.people_named('kim').join(search.visited('seoul').query()
https://www.facebook.com/search/108259475871818/visitors/str/kim/users-named/intersect

find the friends of people who live in australia who also like the ISIS page
search.likers_of('isis').join(search.resides_in('australia').friends.query()
https://www.facebook.com/search/1586149978322999/likers/108191385876482/residents/intersect/friends

find the people who are named "Maria" but also have friends named "Antonio"
search.people_named('maria').friends_with('antonio')
https://www.facebook.com/search/str/maria/users-named/str/antonio/users-named/friends/intersect

"""


BASE = 'https://www.facebook.com/search'


class SearchObject(object):

    def __init__(self, urlcomp):
        self.urlcomp = urlcomp
        self.intersection = False

    def query(self):
        end = '/intersect' if self.intersection else ''
        return '{}{}{}'.format(BASE, self.urlcomp, end)

    def join(self, search):
        self.urlcomp += search.urlcomp
        self.intersect()
        return self

    def intersect(self):
        self.intersection = True
        return self

    def append(self, text):
        self.urlcomp += text
        return self


class PeopleObject(SearchObject):

    def friends(self):
        return self.append('/friends')

    def friends_with(self, name):
        return self.join(friends_with(name))

    def people_named(self, name):
        return self.join(people_named(name))

    def visited(self, place):
        return self.join(visited(place))

    def likes_page(self, page_id):
        return self.join(likes_page(page_id))

    def lives_in(self, place_id):
        return self.join(lives_in(place_id))

    def male(self):
        return self.join(male())

    def female(self):
        return self.join(female())


class PageObject(SearchObject):

    def __init__(self, page):
        if page.isdigit():
            base = '/' + page
        else:
            base = '/str/{}/pages-named'.format(page)
        SearchObject.__init__(self, base)

    def likers(self):
        return PeopleObject(self.urlcomp).append('/likers')


class PlaceObject(PageObject):

    def __init__(self, place):
        PageObject.__init__(self, place)

    def lives_in(self):
        return PeopleObject(self.urlcomp).append('/residents/present')

    def lived_in(self):
        return PeopleObject(self.urlcomp).append('/residents/past')

    def visited(self):
        return PeopleObject(self.urlcomp).append('/visitors')


class NamedPerson(PeopleObject):

    def __init__(self, name):
        base = '/str/{}/users-named'.format(name)
        PeopleObject.__init__(self, base)





def male():
    return PeopleObject('/males').intersect()


def female():
    return PeopleObject('/females').intersect()


def lived_in(place):
    return PlaceObject(place).lived_in()


def lives_in(place):
    return PlaceObject(place).lives_in()


def visited(place):
    return PlaceObject(place).visited()


def friends_with(name):
    return NamedPerson(name).friends()


def pages_named(name):
    return PageObject(name)


def people_named(name):
    return NamedPerson(name)


def likes_page(page_id):
    return PageObject(page_id).likers()



if __name__ == '__main__':
    # people named daniel, who are friends with a henry, who has been to sydney
    print(people_named('Daniel').friends_with('Henry').visited('110884905606108').query())
    # people named daniel, who are friends with a henry, who has been to melbourne
    print(people_named('Daniel').friends_with('Henry').visited('melbourne').query())
    # people named daniel, who are friends with a henry and also friends with a tom
    print(people_named('Daniel').friends_with('Henry').friends_with('Tom').query())
    # people who like ISIS
    print(likes_page('1586149978322999').friends_with('John').query())
