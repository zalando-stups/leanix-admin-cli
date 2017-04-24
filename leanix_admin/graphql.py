list_tag_groups = '''
query {
  listTagGroups: allTagGroups {
    edges {
      node {
        id
        name
        shortName
        description
        mode
        restrictToFactSheetTypes
        tags {
          edges {
            node {
              id
              name
              description
              color
              status
            }
          }
        }
      }
    }
  }
}
'''

create_tag_group = '''
mutation ($name: String!,
          $mode:TagGroupModeEnum!,
          $restrictToFactSheetTypes: [FactSheetType!]!,
          $shortName: String,
          $description: String) {
  createTagGroup(name: $name,
                 mode: $mode, 
                 restrictToFactSheetTypes: $restrictToFactSheetTypes,
                 shortName: $shortName,
                 description: $description) {
    id
  }
}
'''

update_tag_group = '''
mutation ($id: ID!,
          $patches: [Patch]!) {
  updateTagGroup(id: $id,
                 patches: $patches) {
    id
  }
}
'''

delete_tag_group = '''
mutation ($id: ID!) {
  deleteTagGroup (id: $id){
    id
  }
}
'''

create_tag = '''
mutation ($name: String!,
          $description: String,
          $color: String!,
          $tagGroupId: ID!) {
  createTag(name: $name,
            description: $description,
            color: $color,
            tagGroupId: $tagGroupId) {
    id
  }
}
'''

update_tag = '''
mutation ($id: ID!
          $patches: [Patch]!) {
  updateTag(id: $id,
            patches: $patches) {
    id
  }
}
'''

delete_tag = '''
mutation ($id: ID!) {
  deleteTag(id: $id) {
    id
  }
}
'''
