extern crate osmpbfreader;

use std::collections::HashMap;
use std::env::args;

fn process_file(filename : &String, itemname : &String) {
    let r = std::fs::File::open(&std::path::Path::new(filename)).unwrap();
    //println!("Parsing {:?}...",filename);
    let mut pbf = osmpbfreader::OsmPbfReader::new(r);
    let objs = pbf.get_objs_and_deps(|obj| {
       (obj.is_way() && obj.tags().contains_key("name") && obj.tags().get("name").unwrap()==itemname)
    }).unwrap();
    //println!("Objs got: {:?}", objs.len());
    let mut nodes = HashMap::new();

    for (_id, obj) in &objs {
        match obj {
            osmpbfreader::OsmObj::Node(n) => {
                nodes.insert( n.id, (n.lat(),n.lon()) );
            }
            osmpbfreader::OsmObj::Way(w) => {
                let mut path = Vec::new();
                for node_id in &w.nodes {
                    match nodes.get(&node_id) {
                        Some(node) => path.push((node.0,node.1)),
                        None => { panic!(); }
                    }
                }
                println!("{}\npath", w.tags.get("name").unwrap());
                for node in path {
                    println!("  {} {}", node.1, node.0);
                }
                println!("END\nEND");
//                println!("{:?}", path);
            },
            osmpbfreader::OsmObj::Relation(_) => ()
        }
    }
}

fn main() {
    let filename;
    let itemname; 
    match args().nth(1) {
      Some(v) => filename = v,
      None => { panic!("You must give File Name as first argument"); }
    }
    match args().nth(2) {
      Some(v) => itemname = v,
      None => { panic!("You must give Item Name as second argument"); }
    }
    process_file(&filename, &itemname);
}

