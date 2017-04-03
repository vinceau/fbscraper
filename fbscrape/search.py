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


class PeopleObject(SearchObject):

    def friends_with(self, name):
        return PeopleObject(self.urlcomp + friends_with(name).urlcomp).intersect()

    def people_named(self, name):
        return PeopleObject(self.urlcomp + people_named(name).urlcomp).intersect()

    def visited(self, place_id):
        return PeopleObject(self.urlcomp + visited(place_id).urlcomp).intersect()

    def likes_page(self, page_id):
        return PeopleObject(self.urlcomp + likes_page(page_id).urlcomp).intersect()

    def lives_in(self, place_id):
        return PeopleObject(self.urlcomp + lives_in(place_id).urlcomp).intersect()


def lives_in(place_id):
    return PeopleObject('/{}/residents'.format(place_id))


def visited(place_id):
    return PeopleObject('/{}/visitors'.format(place_id))


def friends_with(name):
    return PeopleObject('/str/{}/users-named/friends'.format(name))


def people_named(name):
    return PeopleObject('/str/{}/users-named'.format(name))


def likes_page(page_id):
    return PeopleObject('/{}/likers'.format(page_id))



if __name__ == '__main__':
    # people named daniel, who are friends with a henry, who has been to sydney
    print(people_named('Daniel').friends_with('Henry').visited('110884905606108').query())
    # people who like ISIS
    print(likes_page('1586149978322999').friends_with('John').query())
