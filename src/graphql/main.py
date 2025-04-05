from graphene import Schema, ObjectType, String

class Query(ObjectType):
    hello = String(name=String(default_value="world"))

    def resolve_hello(self, info, name):
        return f"Hello {name}"
    

schema = Schema(query=Query)

gql = '''
{
    hello(name: "graphql")
}
'''

if __name__ == '__main__':
    result = schema.execute(gql)
    print(result)
