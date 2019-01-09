require "weird_al"
require "halite"
include WeirdAl

def get_config
  data = Workflow.load_data("config")
  data ? 
    Hash(String, String).from_json(data) 
    : {} of String => String
end

def load_pipelines
  data = Workflow.load_data("pipelines")
  return Array(Item).from_json(data) if data

  config = get_config
  base_url = config["base_url"]
  url = "#{base_url}/go/api/config/pipeline_groups"
  username = config["username"]
  password = Workflow.get_password("alfred-gocd-pw")

  response = Halite.basic_auth(user: username, pass: password).get(url)
  pipelines = JSON.parse(response.body).as_a.flat_map { |group| group["pipelines"].as_a }
  items = pipelines.map do |pipeline|
    item = Item.new pipeline["name"].as_s
    pipeline_url = "#{base_url}/go/tab/pipeline/history/#{item.title}"
    item.arg = pipeline_url
    item.uid = pipeline_url
    item.subtitle = pipeline_url
    item
  end
  Workflow.store_data("pipelines", items.to_json)
  items
end

handle "--auth-un" do |args|
  config = get_config
  username = args[1]
  config["username"] = username
  Workflow.store_data("config", config.to_json)
end

handle "--auth-pw" do |args|
  pw = args[1..-1].join(" ")
  Workflow.save_password("alfred-gocd-pw", pw)
  nil
end

handle "--baseurl" do |args|
  config = get_config
  base_url = args[1]
  config["base_url"] = base_url
  Workflow.store_data("config", config.to_json)
end

handle "--refresh" do |args|
  Workflow.delete_data("pipelines")
  load_pipelines
  nil
end

handle do |args|
  load_pipelines
end

handle /.*/ do |args|
  pipelines = load_pipelines
  query = args[0]
  Workflow.search(query, pipelines, &.title)
end

Workflow.run
