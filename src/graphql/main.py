from graphene import Schema, ObjectType, String, Int, Field


class UserType(ObjectType):
    id = Int()
    name = String()
    age = Int()


class Query(ObjectType):
    user = Field(UserType, user_id=Int())

    users = [
        {'id':1, 'name': 'Test1', 'age':30},
        {'id':2, 'name': 'Test2', 'age':31},
        {'id':3, 'name': 'Test3', 'age':32},
        {'id':4, 'name': 'Test4', 'age':33}
    ]

    def resolve_user(self, info, user_id):
        matched_users = [user for user in Query.users if user['id'] == user_id]
        return matched_users[0] if matched_users else None


schema = Schema(query=Query)

gql = '''
query {
    user(userId: 2) {
        id
        name
        age
    }
}
'''

if __name__ == '__main__':
    result = schema.execute(gql)
    print(result)
