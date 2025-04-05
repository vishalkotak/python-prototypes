from graphene import Schema, ObjectType, String, Int, Field, List, Mutation

class UserType(ObjectType):
    id = Int()
    name = String()
    age = Int()

# Mutation to create a new user
class CreateUser(Mutation):
    class Arguments:
        name = String(required=True)
        age = Int(required=True)

    user = Field(UserType)

    def mutate(self, info, name, age):
        user = {'id': len(Query.users) + 1, 'name': name, 'age': age}
        Query.users.append(user)
        return CreateUser(user=user)

# Query to get users
class Query(ObjectType):
    user = Field(UserType, user_id=Int())
    user_by_min_age = List(UserType, min_age=Int())

    users = [
        {'id': 1, 'name': 'Test1', 'age': 30},
        {'id': 2, 'name': 'Test2', 'age': 31},
        {'id': 3, 'name': 'Test3', 'age': 32},
        {'id': 4, 'name': 'Test4', 'age': 33}
    ]

    def resolve_user(self, info, user_id):
        matched_users = [user for user in Query.users if user['id'] == user_id]
        return matched_users[0] if matched_users else None

    def resolve_user_by_min_age(self, info, min_age):
        matched_users = [user for user in Query.users if user['age'] >= min_age]
        return matched_users

# Mutation class for Graphene
class Mutation(ObjectType):
    create_user = CreateUser.Field()

# Define the schema
schema = Schema(query=Query, mutation=Mutation)

gql1 = '''
mutation {
    createUser(name: "Test5", age: 35) {
        user {
            id
            name
            age
        }
    }
}
'''

gql2 = '''
query {
    user(userId: 5) {
        id
        name
        age
    }
}
'''

if __name__ == '__main__':
    result = schema.execute(gql1)
    print(result.data)
    result = schema.execute(gql2)
    print(result.data)
